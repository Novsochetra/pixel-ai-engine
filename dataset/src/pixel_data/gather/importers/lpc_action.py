import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterator

from PIL import Image

from pixel_data.records import Record
from pixel_data.sources import Source

FRAME = 64
SHEET = (9 * FRAME, 12 * FRAME)

# Each action takes four rows, one per direction, in this order. Checked against the lpc-4view
# sheet of the same character: the first row faces right, the second faces left.
DIRECTIONS = ("right", "left", "front", "back")
ACTIONS = (("walk", 0, 9), ("thrust", 4, 8), ("slash", 8, 6))


def sheet_records(source: Source, zip_path: Path, raw: Path, member: str) -> Iterator[Record]:
    # The same number as in lpc-4view is the same character, but it gets its own name here so an
    # export of one source never mixes in the other's pictures.
    character = f"lpc-action/{Path(member).stem}"

    for action, first_row, frames in ACTIONS:
        for offset, view in enumerate(DIRECTIONS):
            # One record per action and direction: a strip of its frames, left to right.
            top = (first_row + offset) * FRAME
            yield Record(
                id=f"{character}/{action}/{view}",
                source=source.id,
                character=character,
                view=view,
                action=action,
                width=frames * FRAME,
                height=FRAME,
                file=str(zip_path.relative_to(raw)),
                member=member,
                crop=f"0,{top},{frames * FRAME},{FRAME}",
                license=source.license,
                use=source.use,
                source_split="train",
            )


def read(source: Source, folder: Path, raw: Path, skipped: Counter) -> Iterator[Record]:
    zip_path = folder / "images" / "train.zip"

    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if not member.endswith(".png"):
                continue

            with archive.open(member) as handle:
                size = Image.open(handle).size

            if size != SHEET:
                skipped[f"sheet is not {SHEET[0]}x{SHEET[1]}"] += 1
                continue

            yield from sheet_records(source, zip_path, raw, member)
