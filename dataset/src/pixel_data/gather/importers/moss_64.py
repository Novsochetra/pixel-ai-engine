import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

from pixel_data.records import Record
from pixel_data.sources import Source

SPLITS = ("train", "validation")

# The prompt asked for a view in words. Checked in order: the first rule whose words all appear wins.
# "left" means the subject faces the left of the picture, as in the LPC sheets.
VIEW_RULES = (
    (("front and left side",), "front-left"),
    (("front and right side",), "front-right"),
    (("side view", "left"), "left"),
    (("side view", "right"), "right"),
    (("three-quarter", "left"), "front-left"),
    (("three-quarter", "right"), "front-right"),
    (("front view",), "front"),
    (("face-on",), "front"),
    (("from the front",), "front"),
)

SUBJECT = re.compile(r"depicting (.+?)\.(?: |$)")


def view_of(requested: str) -> str | None:
    words = requested.lower()

    for needed, view in VIEW_RULES:
        if all(word in words for word in needed):
            return view

    return None


def caption_of(prompt: str) -> str:
    # The prompt is mostly about the canvas and the magenta background; keep only the subject.
    found = SUBJECT.search(prompt)

    return found.group(1) if found else prompt


def row_record(source: Source, folder: Path, raw: Path, split: str, row: dict) -> Record:
    return Record(
        id=f"moss-64/{row['id']}",
        source=source.id,
        character=f"moss-64/{row['split_group']}",
        view=view_of(row["requested_view"]),
        width=row["width"],
        height=row["height"],
        file=str((folder / split / row["file_name"]).relative_to(raw)),
        caption=caption_of(row["text"]),
        license=source.license,
        use=source.use,
        source_split=split,
    )


def read(source: Source, folder: Path, raw: Path, skipped: Counter) -> Iterator[Record]:
    for split in SPLITS:
        with (folder / split / "metadata.jsonl").open() as handle:
            for line in handle:
                row = json.loads(line)

                if not (folder / split / row["file_name"]).is_file():
                    skipped["image file is missing"] += 1
                    continue

                yield row_record(source, folder, raw, split, row)
