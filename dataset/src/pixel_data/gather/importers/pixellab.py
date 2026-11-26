import json
from collections import Counter
from pathlib import Path
from typing import Iterator

from PIL import Image

from pixel_data.records import Record
from pixel_data.sources import Source

# PixelLab's west faces the left of the picture, the same as "left" everywhere else.
VIEW_OF_DIRECTION = {
    "south": "front",
    "north": "back",
    "west": "left",
    "east": "right",
    "south-west": "front-left",
    "south-east": "front-right",
    "north-west": "back-left",
    "north-east": "back-right",
}


def view_record(source: Source, raw: Path, card: dict, view: str, image: Path) -> Record:
    with Image.open(image) as picture:
        width, height = picture.size

    return Record(
        id=f"pixellab/{card['id']}/{view}",
        source=source.id,
        character=f"pixellab/{card['id']}",
        view=view,
        width=width,
        height=height,
        file=str(image.relative_to(raw)),
        caption=card["description"],
        license=source.license,
        use=source.use,
    )


def read_character(source: Source, folder: Path, raw: Path, card: dict, skipped: Counter) -> Iterator[Record]:
    for direction, name in card["files"].items():
        image = folder / name

        if direction not in VIEW_OF_DIRECTION:
            skipped["unknown direction"] += 1
        elif not image.is_file():
            skipped["image file is missing"] += 1
        else:
            yield view_record(source, raw, card, VIEW_OF_DIRECTION[direction], image)


def read(source: Source, folder: Path, raw: Path, skipped: Counter) -> Iterator[Record]:
    for plan in sorted(path for path in folder.iterdir() if path.is_dir()):
        if not (plan / "character.json").is_file():
            skipped["not finished"] += 1
            continue

        card = json.loads((plan / "character.json").read_text())
        yield from read_character(source, plan, raw, card, skipped)
