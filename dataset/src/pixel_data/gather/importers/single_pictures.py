"""Sources with one picture and one caption per parquet row: icons, items and scenes."""

from collections import Counter
from pathlib import Path
from typing import Iterator

from pixel_data.gather.importers.parquet_rows import pictures, single_record
from pixel_data.records import Record
from pixel_data.sources import Source


def split_of(path: Path) -> str:
    # train-00001-of-00004, val_unseen-00000-of-00001 -> train, val_unseen
    return path.stem.split("-")[0]


def read(source: Source, folder: Path, raw: Path, skipped: Counter) -> Iterator[Record]:
    for path in sorted((folder / "data").glob("*.parquet")):
        for picture in pictures(path, "image", ["caption"], skipped):
            yield single_record(source, path, raw, picture, picture.fields["caption"], split_of(path))
