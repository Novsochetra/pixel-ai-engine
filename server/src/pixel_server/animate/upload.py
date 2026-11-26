from pathlib import Path

from pixel_data.dashboard import animate_page as animate
from pixel_data.dashboard.studio import Invalid

from pixel_server.animate.animate_options import upload_source

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class TooBig(ValueError):
    pass


# A body read in chunks, so a huge upload is cut off at the limit and never held whole.
async def read_capped(chunks, limit: int) -> bytes:
    body = bytearray()

    async for chunk in chunks:
        body += chunk

        if len(body) > limit:
            raise TooBig(f"Too big: upload at most {limit // 1_000_000} MB.")

    return bytes(body)


# Pillow reads a JPEG as well, but the form asks for a PNG, so a PNG is all it keeps.
def save_png(data: Path, name: str, body: bytes) -> dict:
    if not body.startswith(PNG_SIGNATURE):
        raise Invalid("The file is not a PNG. Upload a PNG.")

    path = animate.save_upload(data, name, body)

    return upload_source(path.name)
