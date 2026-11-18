import tarfile
from collections import Counter
from pathlib import Path
from typing import Iterator

from PIL import Image

from pixel_data.records import Record
from pixel_data.sources import Source

VIEWS = {"front", "back", "left", "right"}


def split_of(tar: Path) -> str:
    return tar.stem.split("-")[1]


def member_record(source: Source, tar: Path, raw: Path, member: tarfile.TarInfo, size: tuple[int, int]) -> Record:
    number, view, _ = member.name.split(".")
    split = split_of(tar)
    character = f"pac/{split}/{number}"

    return Record(
        id=f"{character}/{view}",
        source=source.id,
        character=character,
        view=view,
        width=size[0],
        height=size[1],
        file=str(tar.relative_to(raw)),
        member=member.name,
        data_offset=member.offset_data,
        data_length=member.size,
        license=source.license,
        use=source.use,
        source_split=split,
    )


def read_tar(source: Source, tar: Path, raw: Path, skipped: Counter) -> Iterator[Record]:
    with tarfile.open(tar) as archive:
        for member in archive:
            parts = member.name.split(".")

            if not member.isfile() or len(parts) != 3 or parts[1] not in VIEWS:
                skipped["file is not <number>.<view>.png"] += 1
                continue

            size = Image.open(archive.extractfile(member)).size
            yield member_record(source, tar, raw, member, size)


def read(source: Source, folder: Path, raw: Path, skipped: Counter) -> Iterator[Record]:
    for tar in sorted(folder.glob("pac-*.tar")):
        yield from read_tar(source, tar, raw, skipped)
