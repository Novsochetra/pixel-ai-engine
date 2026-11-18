import csv
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterator

from PIL import Image

from pixel_data.records import Record
from pixel_data.sources import Source

SHEET = 128
VIEW = 64
QUADRANTS = (("back", 0, 0), ("left", VIEW, 0), ("front", 0, VIEW), ("right", VIEW, VIEW))
SHEET_WORDS = ", 4-view sprite sheet"


def read_captions(folder: Path) -> dict[str, str]:
    with (folder / "captions" / "captions_optimized.csv").open(newline="") as handle:
        rows = csv.DictReader(handle)

        # The caption describes the whole 2x2 sheet; each record is one view of it.
        return {row["image_path"]: row["text"].split(SHEET_WORDS)[0] for row in rows}


def sheet_records(source: Source, zip_path: Path, raw: Path, member: str, caption: str | None) -> Iterator[Record]:
    character = f"lpc-4view/{Path(member).stem}"

    for view, left, top in QUADRANTS:
        yield Record(
            id=f"{character}/{view}",
            source=source.id,
            character=character,
            view=view,
            width=VIEW,
            height=VIEW,
            file=str(zip_path.relative_to(raw)),
            member=member,
            crop=f"{left},{top},{VIEW},{VIEW}",
            caption=caption,
            license=source.license,
            use=source.use,
            source_split="train",
        )


def read(source: Source, folder: Path, raw: Path, skipped: Counter) -> Iterator[Record]:
    captions = read_captions(folder)
    zip_path = folder / "images" / "train.zip"

    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if not member.endswith(".png"):
                continue

            with archive.open(member) as handle:
                size = Image.open(handle).size

            if size != (SHEET, SHEET):
                skipped[f"sheet is not {SHEET}x{SHEET}"] += 1
                continue

            yield from sheet_records(source, zip_path, raw, member, captions.get(Path(member).name))
