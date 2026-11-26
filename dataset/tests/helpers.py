import csv
import io
import json
import tarfile
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

from pixel_data.sources import Layout, Source

QUADRANT_COLORS = {
    "back": (255, 0, 0, 255),
    "left": (0, 255, 0, 255),
    "front": (0, 0, 255, 255),
    "right": (255, 255, 0, 255),
}


def png_bytes(size: int = 8, color: tuple = (200, 40, 40, 255)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGBA", (size, size), color).save(buffer, format="PNG")

    return buffer.getvalue()


def write_parquet(path, captions: list[str]) -> None:
    images = [{"bytes": png_bytes(), "path": None} for _ in captions]
    table = pa.table({"image": images, "caption": captions})

    pq.write_table(table, path)


def mark_gathered(folder: Path) -> None:
    (folder / "_source.json").write_text(json.dumps({"gathered_at": "2026-11-18T09:00:00+00:00"}))


def fake_pac(layout: Layout) -> Source:
    source = Source("pac", "huggingface", "CC-BY-NC-4.0", "train", ["rotate"])
    folder = layout.source_dir(source)
    folder.mkdir(parents=True)

    for split, numbers in (("train", (0, 1)), ("test", (0,))):
        with tarfile.open(folder / f"pac-{split}-000000.tar", "w") as archive:
            for number in numbers:
                for shade, view in enumerate(("back", "left", "front", "right")):
                    add_to_tar(archive, f"{number}.{view}.png", png_bytes(64, (shade * 60, number * 90, 10, 255)))
            add_to_tar(archive, "notes.txt", b"not a view")

    mark_gathered(folder)

    return source


def add_to_tar(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    archive.addfile(info, io.BytesIO(data))


def lpc_sheet() -> bytes:
    sheet = Image.new("RGBA", (128, 128))
    corners = {"back": (0, 0), "left": (64, 0), "front": (0, 64), "right": (64, 64)}

    for view, corner in corners.items():
        sheet.paste(Image.new("RGBA", (64, 64), QUADRANT_COLORS[view]), corner)

    buffer = io.BytesIO()
    sheet.save(buffer, format="PNG")

    return buffer.getvalue()


def fake_lpc_4view(layout: Layout) -> Source:
    source = Source("lpc-4view", "huggingface", "CC-BY-SA-3.0", "train", ["rotate"])
    folder = layout.source_dir(source)
    (folder / "images").mkdir(parents=True)
    (folder / "captions").mkdir()

    with zipfile.ZipFile(folder / "images" / "train.zip", "w") as archive:
        archive.writestr("train/char_00000.png", lpc_sheet())
        archive.writestr("train/char_00001.png", png_bytes(100))

    with (folder / "captions" / "captions_optimized.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["image_path", "text"])
        writer.writerow(["char_00000.png", "lpc-style pixel art character, with spear, 4-view sprite sheet (front/back/left/right)"])

    mark_gathered(folder)

    return source


ACTION_ROWS = ("right", "left", "front", "back")


def action_sheet() -> bytes:
    # Each row is one colour per direction, so a test can tell the strips apart.
    sheet = Image.new("RGBA", (576, 768))
    for row in range(12):
        color = QUADRANT_COLORS[ACTION_ROWS[row % 4]]
        sheet.paste(Image.new("RGBA", (576, 64), color), (0, row * 64))

    buffer = io.BytesIO()
    sheet.save(buffer, format="PNG")

    return buffer.getvalue()


def fake_lpc_action(layout: Layout) -> Source:
    source = Source("lpc-action", "huggingface", "CC-BY-SA-3.0", "train", ["animate"])
    folder = layout.source_dir(source)
    (folder / "images").mkdir(parents=True)

    with zipfile.ZipFile(folder / "images" / "train.zip", "w") as archive:
        archive.writestr("images/", b"")
        archive.writestr("images/char_00000.png", action_sheet())
        archive.writestr("images/char_00001.png", png_bytes(128))

    mark_gathered(folder)

    return source


MOSS_PROMPT = "A single game sprite designed for a native 64x64 pixel grid, depicting {}. The full body is shown. Use a magenta background."


def fake_moss_64(layout: Layout) -> Source:
    source = Source("moss-64", "huggingface", "Apache-2.0", "eval", ["create", "rotate"])
    folder = layout.source_dir(source)
    rows = {
        "train": [
            ("characters-cook-v01", "characters-cook", "a cook in a white hat", "in three-quarter view facing left."),
            ("characters-cook-v02", "characters-cook", "a cook in a white hat", "in three-quarter view facing right."),
            ("food-pie-v01", "food-pie", "an apple pie", "The entire item is shown at a shallow three-quarter angle."),
        ],
        "validation": [("vehicles-cart-v01", "vehicles-cart", "a wooden cart", "in side view, with its front pointing left.")],
    }

    for split, entries in rows.items():
        (folder / split / "images").mkdir(parents=True)
        with (folder / split / "metadata.jsonl").open("w") as handle:
            for number, (row_id, group, subject, view) in enumerate(entries):
                name = f"images/{row_id}.png"
                (folder / split / name).write_bytes(png_bytes(64, (number * 50, 80, 40, 255)))
                row = {"id": row_id, "split_group": group, "text": MOSS_PROMPT.format(subject),
                       "requested_view": view, "file_name": name, "width": 64, "height": 64}
                handle.write(json.dumps(row) + "\n")

        # A row whose picture is not there.
        with (folder / split / "metadata.jsonl").open("a") as handle:
            handle.write(json.dumps({"id": f"gone-{split}", "split_group": "gone", "text": "", "requested_view": "",
                                     "file_name": "images/gone.png", "width": 64, "height": 64}) + "\n")

    mark_gathered(folder)

    return source


def picture_table(sizes: list[int], colors: list[tuple], **columns) -> pa.Table:
    images = [{"bytes": png_bytes(size, color), "path": None} for size, color in zip(sizes, colors)]

    return pa.table({"image": images, **columns})


def fake_icons(layout: Layout) -> Source:
    source = Source("icons-172k", "huggingface", "MIT", "train", ["create"])
    data = layout.source_dir(source) / "data"
    data.mkdir(parents=True)

    reds = [(index * 20, 0, 0, 255) for index in range(5)]
    table = picture_table([32] * 5, reds, caption=[f"pixel art icon of thing {index}" for index in range(5)])
    pq.write_table(table, data / "train-00000-of-00001.parquet", row_group_size=2)

    empty = pa.table({"image": pa.array([None], pa.struct([("bytes", pa.binary()), ("path", pa.string())])), "caption": ["gone"]})
    pq.write_table(empty, data / "val_unseen-00000-of-00001.parquet")

    mark_gathered(layout.source_dir(source))

    return source


def fake_landscapes(layout: Layout) -> Source:
    source = Source("landscapes-20k", "huggingface", "Apache-2.0", "train", ["landscape"])
    data = layout.source_dir(source) / "data"
    data.mkdir(parents=True)

    columns = {"id": ["0000000", "0000001"], "prompt": ["a snowy pass", "a warm beach"]}
    for size in (64, 128, 256):
        images = [{"bytes": png_bytes(size, (0, 0, number + 1, 255)), "path": None} for number in range(2)]
        columns[f"image_processed_{size}"] = images
    pq.write_table(pa.table(columns), data / "train-00000-of-00001.parquet")

    mark_gathered(layout.source_dir(source))

    return source


def write_pixellab_character(folder: Path, plan: str, description: str, directions: list[str]) -> None:
    (folder / plan / "rotations").mkdir(parents=True)
    files = {}

    for number, direction in enumerate(directions):
        name = f"rotations/{direction}.png"
        (folder / plan / name).write_bytes(png_bytes(64, (number * 40, 60, 90, 255)))
        files[direction] = name

    card = {"id": plan, "group": plan.split("-")[0], "body": "humanoid", "description": description,
            "character_id": f"id-{plan}", "size": {"width": 64, "height": 64}, "files": files}
    (folder / plan / "character.json").write_text(json.dumps(card))


def fake_pixellab(layout: Layout) -> Source:
    source = Source("pixellab", "pixellab", "PixelLab output", "hold", ["create", "rotate"],
                    links=["https://www.pixellab.ai/termsofservice"])
    folder = layout.source_dir(source)
    folder.mkdir(parents=True)

    write_pixellab_character(folder, "fantasy-001", "a knight in silver armour with a red cape",
                             ["south", "west", "east", "north"])
    write_pixellab_character(folder, "scifi-001", "a pilot in an orange suit", ["south", "south-east", "north-west"])
    (folder / "scifi-002" / "rotations").mkdir(parents=True)
    (folder / "scifi-002" / "job.json").write_text("{}")
    (folder / "failed.jsonl").write_text("")

    mark_gathered(folder)

    return source
