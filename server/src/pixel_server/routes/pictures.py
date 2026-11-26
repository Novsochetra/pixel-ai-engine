from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse

from pixel_server.library.pictures import file_under, image_png

router = APIRouter()

# A record never changes its picture without a new import, so the browser may keep it a while.
CACHE = {"Cache-Control": "private, max-age=3600"}
MEDIA_TYPES = {".png": "image/png", ".gif": "image/gif"}


def png(request: Request, image_id: str, thumb: bool) -> Response:
    body = image_png(request.app.state.layout.data, image_id, thumb)

    if body is None:
        raise HTTPException(404, f"No image {image_id}.")

    return Response(body, media_type="image/png", headers=CACHE)


@router.get("/api/images/{image_id:path}.png")
def image(request: Request, image_id: str) -> Response:
    return png(request, image_id, thumb=False)


@router.get("/api/thumbs/{image_id:path}.png")
def thumb(request: Request, image_id: str) -> Response:
    return png(request, image_id, thumb=True)


@router.get("/api/files/{folder}/{path:path}")
def file(request: Request, folder: str, path: str) -> FileResponse:
    target = file_under(request.app.state.layout.data, folder, path)

    if target is None:
        raise HTTPException(404, "Not found.")

    return FileResponse(target, media_type=MEDIA_TYPES[target.suffix])
