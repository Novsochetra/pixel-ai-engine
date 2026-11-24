"""Cut the OpenGameArt sprite sheets into single sprites, ready to be labelled.

    uv run --with numpy --with scipy --with zstandard python opengameart/cut.py data/opengameart

Reads data/raw/opengameart-2d (the zips and 2D_Art.jsonl.zst with one line per page). Keeps the pages
that look like characters (by their tags, collections and title), opens their PNG and GIF files, also
the ones in a zip inside a zip, and cuts every sheet into its separate shapes. A shape is kept when
it has the size and form of a standing character. Animation frames are nearly the same picture, so
only one shape per set of colours is kept per page
(a pack often saves every frame as its own file), at most 6 per sheet and 40 per page.

Each sprite is put on a 64 x 64 clear square, made bigger by a whole number (so the pixels stay
square), standing on the bottom like the LPC sprites. Writes <out>/sprites/<n>.png and
<out>/sprites.jsonl: {"n", "page", "title", "author", "file", "box"}. All pages are CC0.
"""

import argparse
import collections
import csv
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote

import numpy as np
import zstandard
from PIL import Image
from scipy import ndimage

RAW = Path("data/raw/opengameart-2d")
SIZE = 64
CHARACTER = re.compile(r"character|enem|monster|player|hero|npc|creature|mob\b|villager|knight|"
                       r"wizard|warrior|soldier|zombie|skeleton|goblin|orc|people|person|chibi|avatar|"
                       r"slime|animal|boss|mage|ninja|robot|pirate|elf|dwarf", re.I)
NOT_CHARACTER = re.compile(r"tile|background|font|icon|\bui\b|gui|texture|isometric|3d|vector|svg|"
                           r"portrait|face|card|map|terrain|hud|button|particle|effect|explosion|item|"
                           r"weapon|food|furniture|ship|vehicle|bullet|projectile|object", re.I)
PER_SHEET = 6
PER_PAGE = 40


def read_pages() -> list[dict]:
    stream = zstandard.ZstdDecompressor().stream_reader((RAW / "2D_Art.jsonl.zst").open("rb"))

    return [json.loads(line) for line in io.TextIOWrapper(stream)]


def is_character_page(page: dict) -> bool:
    words = " ".join([page["title"], *page.get("tags", []), *page.get("collections", [])])

    return bool(CHARACTER.search(words)) and not NOT_CHARACTER.search(" ".join(page.get("tags", [])) + " " + page["title"])


def pictures(pages: list[dict]):
    """(page index, file name, image) for every PNG or GIF of a character page."""
    owner = {}
    for index, page in enumerate(pages):
        if is_character_page(page):
            for url in [f["url"] for f in page["files"]] + page.get("preview_images", []):
                owner.setdefault(unquote(url.rsplit("/", 1)[-1]), index)

    for archive in sorted(RAW.glob("2D_Art_*.zip")):
        with zipfile.ZipFile(archive) as outer:
            for info in outer.infolist():
                index = owner.get(info.filename)
                if index is None:
                    continue
                name = info.filename.lower()
                if name.endswith((".png", ".gif")):
                    yield index, info.filename, outer.read(info)
                elif name.endswith(".zip") and info.file_size < 200_000_000:
                    try:
                        with zipfile.ZipFile(io.BytesIO(outer.read(info))) as inner:
                            for item in inner.infolist():
                                if item.filename.lower().endswith(".png") and "__macosx" not in item.filename.lower():
                                    yield index, f"{info.filename}/{item.filename}", inner.read(item)
                    except (zipfile.BadZipFile, NotImplementedError, OSError):
                        continue


def block_size(rgba: np.ndarray) -> int:
    """Art saved bigger than drawn has pixels of k x k blocks; find k so it can be made small again."""
    height, width = rgba.shape[:2]
    for k in (8, 6, 5, 4, 3, 2):
        if height % k == 0 and width % k == 0:
            small = rgba[::k, ::k]
            if np.array_equal(np.repeat(np.repeat(small, k, 0), k, 1), rgba):
                return k

    return 1


def foreground(rgba: np.ndarray) -> np.ndarray:
    """Pixels that are not background: not clear, and not the colour of most of the border."""
    alpha = rgba[..., 3]
    if (alpha < 128).mean() > 0.05:
        return alpha >= 128

    border = np.concatenate([rgba[0], rgba[-1], rgba[:, 0], rgba[:, -1]])
    colours, counts = np.unique(border[:, :3], axis=0, return_counts=True)
    background = colours[counts.argmax()]

    return np.any(np.abs(rgba[..., :3].astype(int) - background) > 8, axis=-1)


def shapes(rgba: np.ndarray):
    """The bounding boxes of separate shapes that could be a standing character, top to bottom."""
    mask = foreground(rgba)
    # Parts a pixel apart (a sword, a hat) belong to the same sprite.
    labels, _ = ndimage.label(ndimage.binary_dilation(mask, iterations=1), structure=np.ones((3, 3)))
    for box in ndimage.find_objects(labels):
        top, bottom, left, right = box[0].start, box[0].stop, box[1].start, box[1].stop
        height, width = bottom - top, right - left
        if not (12 <= height <= 60 and 8 <= width <= 60 and 0.7 <= height / width <= 3):
            continue
        part = mask[top:bottom, left:right]
        colours = len(np.unique(rgba[top:bottom, left:right][part][:, :3], axis=0))
        if part.mean() < 0.3 or colours < 4:
            continue
        yield top, bottom, left, right


def on_square(sprite: np.ndarray, mask: np.ndarray) -> Image.Image:
    sprite = sprite.copy()
    sprite[~mask] = 0
    height, width = sprite.shape[:2]
    scale = max(1, (SIZE - 4) // max(height, width))
    image = Image.fromarray(sprite, "RGBA").resize((width * scale, height * scale), Image.NEAREST)
    square = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    square.alpha_composite(image, ((SIZE - image.width) // 2, SIZE - 2 - image.height))

    return square


def fingerprint(sprite: np.ndarray) -> bytes:
    """A small, rough copy, so frames of one animation count as the same sprite."""
    small = Image.fromarray(sprite, "RGBA").resize((4, 4), Image.BILINEAR)

    return (np.asarray(small) // 64).tobytes()


def palette(sprite: np.ndarray, mask: np.ndarray) -> set:
    return {tuple(c) for c in np.unique(sprite[mask][:, :3] // 16, axis=0)}


def same_character(colours: set, size: tuple[int, int], kept: list[tuple[set, tuple[int, int]]]) -> bool:
    """Frames of one character share their colours and are about the same size. Packs often share
    one palette between characters, so the colours alone are not enough."""
    def near(a, b):
        return abs(a - b) <= max(2, 0.2 * max(a, b))

    return any(len(colours & other) / max(1, len(colours | other)) >= 0.7 and near(size[0], other_size[0])
               and near(size[1], other_size[1]) for other, other_size in kept)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--limit", type=int, default=0, help="stop after this many pictures (0 = all)")
    args = parser.parse_args()

    pages = read_pages()
    (args.out / "sprites").mkdir(parents=True, exist_ok=True)
    seen, kept, counts = set(), [], collections.Counter()
    page_colours = collections.defaultdict(list)  # a pack often saves every frame as its own file
    for done, (index, name, data) in enumerate(pictures(pages), 1):
        if args.limit and done > args.limit:
            break
        counts["pictures"] += 1
        try:
            image = Image.open(io.BytesIO(data))
            image.seek(0)
            rgba = np.asarray(image.convert("RGBA"))
        except Exception:
            counts["unreadable"] += 1
            continue
        if len(page_colours[index]) >= PER_PAGE:
            counts["page has enough"] += 1
            continue
        if rgba.shape[0] * rgba.shape[1] > 16_000_000:
            counts["too big"] += 1
            continue

        k = block_size(rgba)
        rgba = rgba[::k, ::k]
        mask = foreground(rgba)
        found, colours_kept = 0, page_colours[index]
        for top, bottom, left, right in shapes(rgba):
            sprite = rgba[top:bottom, left:right]
            colours = palette(sprite, mask[top:bottom, left:right])
            size = (bottom - top, right - left)
            if same_character(colours, size, colours_kept):
                counts["frame of one kept"] += 1
                continue
            colours_kept.append((colours, size))
            key = fingerprint(np.where(mask[top:bottom, left:right, None], sprite, 0).astype(np.uint8))
            if key in seen:
                counts["same as one kept"] += 1
                continue
            seen.add(key)
            n = len(kept)
            on_square(sprite, mask[top:bottom, left:right]).save(args.out / "sprites" / f"{n}.png")
            page = pages[index]
            kept.append({"n": n, "page": page["url"], "title": page["title"], "author": page["author"],
                         "file": name, "box": [int(left), int(top), int(right), int(bottom)]})
            found += 1
            if found == PER_SHEET or len(colours_kept) >= PER_PAGE:
                break
        counts["pictures with sprites" if found else "pictures without sprites"] += 1
        if done % 500 == 0:
            print(f"{done} pictures, {len(kept)} sprites", flush=True)

    with (args.out / "sprites.jsonl").open("w") as file:
        for item in kept:
            file.write(json.dumps(item) + "\n")
    print(f"{len(kept)} sprites from {counts['pictures']} pictures -> {args.out / 'sprites'}")
    print(dict(counts))


if __name__ == "__main__":
    main()
