import csv
import io
import json
import tarfile
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

from pixel_data.sources import Layout, Source

QUADRANT_COLORS = {
    "back": (255, 0, 0, 255),
    "left": (0, 255, 0, 255),
    "front": (0, 0, 255, 255),
    "right": (255, 255, 0, 255),
}


def png_bytes(size: int = 8, color: tuple = (200, 40, 40, 255)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGBA", (size, size), color).save(buffer, format="PNG")

    return buffer.getvalue()


def write_parquet(path, captions: list[str]) -> None:
    images = [{"bytes": png_bytes(), "path": None} for _ in captions]
    table = pa.table({"image": images, "caption": captions})

    pq.write_table(table, path)


def mark_gathered(folder: Path) -> None:
    (folder / "_source.json").write_text(json.dumps({"gathered_at": "2026-11-18T09:00:00+00:00"}))


def fake_pac(layout: Layout) -> Source:
    source = Source("pac", "huggingface", "CC-BY-NC-4.0", "train", ["rotate"])
    folder = layout.source_dir(source)
    folder.mkdir(parents=True)

    for split, numbers in (("train", (0, 1)), ("test", (0,))):
        with tarfile.open(folder / f"pac-{split}-000000.tar", "w") as archive:
            for number in numbers:
                for shade, view in enumerate(("back", "left", "front", "right")):
                    add_to_tar(archive, f"{number}.{view}.png", png_bytes(64, (shade * 60, number * 90, 10, 255)))
            add_to_tar(archive, "notes.txt", b"not a view")

    mark_gathered(folder)

    return source


def add_to_tar(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    archive.addfile(info, io.BytesIO(data))


def lpc_sheet() -> bytes:
    sheet = Image.new("RGBA", (128, 128))
    corners = {"back": (0, 0), "left": (64, 0), "front": (0, 64), "right": (64, 64)}

    for view, corner in corners.items():
        sheet.paste(Image.new("RGBA", (64, 64), QUADRANT_COLORS[view]), corner)

    buffer = io.BytesIO()
    sheet.save(buffer, format="PNG")

    return buffer.getvalue()


def fake_lpc_4view(layout: Layout) -> Source:
    source = Source("lpc-4view", "huggingface", "CC-BY-SA-3.0", "train", ["rotate"])
    folder = layout.source_dir(source)
    (folder / "images").mkdir(parents=True)
    (folder / "captions").mkdir()

    with zipfile.ZipFile(folder / "images" / "train.zip", "w") as archive:
        archive.writestr("train/char_00000.png", lpc_sheet())
        archive.writestr("train/char_00001.png", png_bytes(100))

    with (folder / "captions" / "captions_optimized.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["image_path", "text"])
        writer.writerow(["char_00000.png", "lpc-style pixel art character, with spear, 4-view sprite sheet (front/back/left/right)"])

    mark_gathered(folder)

    return source
