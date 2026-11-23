import io
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pyarrow.parquet as pq
from PIL import Image

from pixel_data.images import parquet_member
from pixel_data.records import Record
from pixel_data.sources import Source


@dataclass
class Picture:
    """One picture in a parquet file, with the other columns of its row."""

    member: str
    number: int
    size: tuple[int, int]
    fields: dict


def pictures(path: Path, column: str, fields: list[str], skipped: Counter) -> Iterator[Picture]:
    archive = pq.ParquetFile(path)
    number = 0

    for group in range(archive.metadata.num_row_groups):
        table = archive.read_row_group(group, columns=[column, *fields])
        images = table.column(column).combine_chunks().field("bytes").to_pylist()
        values = {name: table.column(name).to_pylist() for name in fields}

        for index, data in enumerate(images):
            if data is None:
                skipped["row has no picture"] += 1
            else:
                size = Image.open(io.BytesIO(data)).size
                row = {name: values[name][index] for name in fields}
                yield Picture(parquet_member(column, group, index), number, size, row)
            number += 1


def single_record(source: Source, path: Path, raw: Path, picture: Picture, caption: str | None, split: str) -> Record:
    # These sources hold one picture per subject, so each picture is its own "character".
    name = f"{source.id}/{path.stem}/{picture.number}"

    return Record(
        id=name,
        source=source.id,
        character=name,
        view=None,
        width=picture.size[0],
        height=picture.size[1],
        file=str(path.relative_to(raw)),
        member=picture.member,
        caption=caption,
        license=source.license,
        use=source.use,
        source_split=split,
    )
