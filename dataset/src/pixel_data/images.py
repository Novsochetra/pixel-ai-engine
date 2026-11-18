import io
import threading
import zipfile
from functools import lru_cache
from pathlib import Path

from PIL import Image


# Opening a zip reads its whole index (50,000 entries for lpc-4view), so keep a few open.
# A ZipFile is not safe to read from two threads at once, hence the lock beside it.
@lru_cache(maxsize=16)
def open_zip(path: Path) -> tuple[zipfile.ZipFile, threading.Lock]:
    return zipfile.ZipFile(path), threading.Lock()


def read_bytes(raw: Path, row) -> bytes:
    path = raw / row["file"]

    if row["data_offset"] is not None:
        with path.open("rb") as handle:
            handle.seek(row["data_offset"])
            return handle.read(row["data_length"])

    if row["member"]:
        return zip_member(path, row["member"])

    return path.read_bytes()


# lpc-4view keeps four views in one sheet, so the same member is asked for four times in a row.
@lru_cache(maxsize=256)
def zip_member(path: Path, member: str) -> bytes:
    archive, lock = open_zip(path)

    with lock:
        return archive.read(member)


def parse_crop(crop: str) -> tuple[int, int, int, int]:
    left, top, width, height = (int(part) for part in crop.split(","))

    return left, top, left + width, top + height


def load_image(raw: Path, row) -> Image.Image:
    image = Image.open(io.BytesIO(read_bytes(raw, row)))
    image = image.convert("RGBA")

    if row["crop"]:
        image = image.crop(parse_crop(row["crop"]))

    return image


def png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue()
