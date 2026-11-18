import io

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image


def png_bytes(size: int = 8, color: tuple = (200, 40, 40, 255)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGBA", (size, size), color).save(buffer, format="PNG")

    return buffer.getvalue()


def write_parquet(path, captions: list[str]) -> None:
    images = [{"bytes": png_bytes(), "path": None} for _ in captions]
    table = pa.table({"image": images, "caption": captions})

    pq.write_table(table, path)
