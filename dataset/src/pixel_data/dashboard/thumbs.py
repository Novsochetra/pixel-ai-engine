import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from pixel_data.dashboard.samples import Sample

THUMB_LIMIT = 256
COLOR_LIMIT = 4096


@dataclass
class Thumb:
    file: str
    width: int
    height: int
    colors: int | None
    caption: str
    origin: str


def count_colors(image: Image.Image) -> int | None:
    colors = image.convert("RGBA").getcolors(maxcolors=COLOR_LIMIT)

    return len(colors) if colors else None


def save_thumb(sample: Sample, target: Path) -> Thumb | None:
    try:
        image = Image.open(io.BytesIO(sample.data))
        image.seek(0)
        image = image.convert("RGBA")
    except Exception:
        return None

    width, height = image.size
    colors = count_colors(image)

    image.thumbnail((THUMB_LIMIT, THUMB_LIMIT), Image.NEAREST)
    image.save(target)

    return Thumb(target.name, width, height, colors, sample.caption, sample.origin)


def save_thumbs(samples: list[Sample], folder: Path) -> list[Thumb]:
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()

    thumbs = [save_thumb(sample, folder / f"{index:03d}.png") for index, sample in enumerate(samples)]

    return [thumb for thumb in thumbs if thumb]
