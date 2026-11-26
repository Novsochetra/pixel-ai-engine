from functools import lru_cache
from pathlib import Path

from PIL import Image
from pixel_data.dashboard import browse_queries as queries
from pixel_data.dashboard.browse_server import open_db
from pixel_data.dashboard.thumbs import THUMB_LIMIT
from pixel_data.images import load_image, png_bytes
from pixel_data.sources import Layout

# The folders /api/files/ serves, and the kinds of file it serves from each.
FILE_FOLDERS = {
    "exports": (".png",),
    "tryouts": (".png",),
    "generated": (".png",),
    "animated": (".png", ".gif"),
    "uploads": (".png",),
}


# A grid asks for the same pictures again on every page turn, and each one is read out of a zip
# or a parquet group, so keep the encoded bytes.
@lru_cache(maxsize=8192)
def image_png(data: Path, image_id: str, thumb: bool) -> bytes | None:
    layout = Layout(data)

    with open_db(layout) as db:
        row = queries.image_row(db, image_id)

        if row is None:
            return None

        image = load_image(layout.raw, row)

    if thumb:
        # Nearest neighbour keeps the pixels square; any other filter blurs pixel art.
        image.thumbnail((THUMB_LIMIT, THUMB_LIMIT), Image.NEAREST)

    return png_bytes(image)


# Only pictures inside those folders: never records.sqlite, a .json or a path with ..
def file_under(data: Path, folder: str, relative: str) -> Path | None:
    if folder not in FILE_FOLDERS:
        return None

    root = (data / folder).resolve()
    target = (root / relative).resolve()

    if not target.is_relative_to(root) or not target.is_file() or target.suffix not in FILE_FOLDERS[folder]:
        return None

    return target
