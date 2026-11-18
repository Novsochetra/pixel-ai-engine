import json
import random
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pyarrow.parquet as pq

IMAGE_SUFFIXES = {".png", ".gif", ".jpg", ".jpeg", ".webp", ".bmp"}
CAPTION_COLUMNS = ("caption", "text", "prompt")
SKIPPED_PARTS = {".cache", ".git", ".idea", ".venv", "_experimental", "previews-8x"}


@dataclass
class Sample:
    data: bytes
    origin: str
    caption: str = ""


def is_image(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_SUFFIXES


def containers(folder: Path) -> list[Path]:
    files = [
        path
        for path in sorted(folder.rglob("*"))
        if path.is_file() and not SKIPPED_PARTS.intersection(path.relative_to(folder).parts)
    ]

    return [path for path in files if path.suffix in {".parquet", ".tar", ".zip"} or is_image(path.name)]


def pick(names: list[str], count: int, rng: random.Random) -> list[str]:
    if len(names) <= count:
        return names

    return sorted(rng.sample(names, count))


def from_zip(path: Path, count: int, rng: random.Random) -> Iterator[Sample]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if is_image(name)]

        for name in pick(names, count, rng):
            yield Sample(archive.read(name), f"{path.name}:{name}")


def from_tar(path: Path, count: int, rng: random.Random) -> Iterator[Sample]:
    with tarfile.open(path) as archive:
        members = [member for member in archive.getmembers() if member.isfile() and is_image(member.name)]
        chosen = set(pick([member.name for member in members], count, rng))

        for member in members:
            if member.name in chosen:
                yield Sample(archive.extractfile(member).read(), f"{path.name}:{member.name}")


def image_column(schema) -> str | None:
    columns = [field.name for field in schema if str(field.type).startswith("struct<bytes")]
    processed = [name for name in columns if "processed" in name]

    return (processed or columns or [None])[0]


def from_parquet(path: Path, count: int) -> Iterator[Sample]:
    table = pq.ParquetFile(path)
    image = image_column(table.schema_arrow)

    if image is None:
        return

    caption = next((name for name in CAPTION_COLUMNS if name in table.schema_arrow.names), None)
    columns = [image] + ([caption] if caption else [])
    batch = next(table.iter_batches(batch_size=count, columns=columns)).to_pylist()

    for row in batch:
        yield Sample(row[image]["bytes"], f"{path.name}", row.get(caption) or "")


def from_container(path: Path, root: Path, count: int, rng: random.Random) -> Iterator[Sample]:
    if path.suffix == ".zip":
        yield from from_zip(path, count, rng)
    elif path.suffix == ".tar":
        yield from from_tar(path, count, rng)
    elif path.suffix == ".parquet":
        yield from from_parquet(path, count)
    else:
        yield Sample(path.read_bytes(), str(path.relative_to(root)))


def folder_captions(folder: Path) -> dict[str, str]:
    captions = {}

    for metadata in folder.rglob("metadata.jsonl"):
        for line in metadata.read_text().splitlines():
            row = json.loads(line)
            captions[row.get("file_name", "")] = row.get("text", "")

    return captions


def caption_for(sample: Sample, captions: dict[str, str]) -> str:
    if sample.caption:
        return sample.caption

    return next((text for name, text in captions.items() if name and sample.origin.endswith(name)), "")


def collect(folder: Path, total: int = 24, seed: int = 7) -> list[Sample]:
    rng = random.Random(seed)
    found = containers(folder)
    loose = [path for path in found if is_image(path.name)]
    packed = [path for path in found if not is_image(path.name)]

    # Loose pictures beside archives are usually the card's illustrations, not the data.
    chosen = pick([str(path) for path in packed], 4, rng) if packed else pick([str(path) for path in loose], total, rng)
    per_container = max(1, total // max(1, len(chosen)))

    samples = []
    for path in chosen:
        samples.extend(from_container(Path(path), folder, per_container, rng))

    captions = folder_captions(folder)
    for sample in samples:
        sample.caption = caption_for(sample, captions)

    return samples[:total]
