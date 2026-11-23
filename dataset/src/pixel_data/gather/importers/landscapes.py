from collections import Counter
from pathlib import Path
from typing import Iterator

from pixel_data.gather.importers.parquet_rows import pictures
from pixel_data.records import Record
from pixel_data.sources import Source

# Each scene comes palette-snapped at three sizes. The 512 px original is not pixel art, so it is left out.
SIZES = (64, 128, 256)


def read(source: Source, folder: Path, raw: Path, skipped: Counter) -> Iterator[Record]:
    for path in sorted((folder / "data").glob("*.parquet")):
        for size in SIZES:
            for picture in pictures(path, f"image_processed_{size}", ["id", "prompt"], skipped):
                scene = f"{source.id}/{picture.fields['id']}"

                yield Record(
                    id=f"{scene}/{size}",
                    source=source.id,
                    character=scene,
                    view=None,
                    width=picture.size[0],
                    height=picture.size[1],
                    file=str(path.relative_to(raw)),
                    member=picture.member,
                    caption=picture.fields["prompt"],
                    license=source.license,
                    use=source.use,
                    source_split="train",
                )
