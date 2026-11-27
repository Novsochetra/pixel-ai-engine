from fastapi import APIRouter, HTTPException, Request
from pixel_data.dashboard.animate import UPLOAD_LIMIT, animate_job
from pixel_data.dashboard.studio import Invalid
from starlette.concurrency import run_in_threadpool

from pixel_server.animate.animate_form import old_form
from pixel_server.animate.animate_options import animate_options, animate_sources, upload_list
from pixel_server.animate.animated_list import animated_list
from pixel_server.animate.upload import TooBig, read_capped, save_png
from pixel_server.routes.jobs import latest_view

router = APIRouter()


@router.get("/api/animated")
def animated(request: Request) -> dict:
    return animated_list(request.app.state.layout.data)


@router.get("/api/animate/options")
def options() -> dict:
    return animate_options()


@router.get("/api/animate/sources")
def sources(request: Request) -> dict:
    return animate_sources(request.app.state.layout.data)


# A plain def, so FastAPI runs it on a worker thread while the job's process starts.
@router.post("/api/animate")
def animate(request: Request, body: dict) -> dict:
    try:
        title, args = animate_job(request.app.state.layout.data, old_form(body))
        request.app.state.jobs.start("animate", title, args)
    except Invalid as error:
        raise HTTPException(400, str(error)) from error
    except RuntimeError as error:
        raise HTTPException(409, str(error)) from error

    return latest_view(request)


@router.get("/api/uploads")
def uploads(request: Request) -> dict:
    return upload_list(request.app.state.layout.data)


# The PNG is the whole body: FastAPI's multipart forms need a package this project does not have.
@router.post("/api/uploads")
async def upload(request: Request, name: str = "upload.png") -> dict:
    if request.headers.get("content-type", "").split(";")[0].strip() != "image/png":
        raise HTTPException(415, "Upload a PNG.")

    if int(request.headers.get("content-length") or 0) > UPLOAD_LIMIT:
        raise HTTPException(413, f"Too big: upload at most {UPLOAD_LIMIT // 1_000_000} MB.")

    try:
        body = await read_capped(request.stream(), UPLOAD_LIMIT)
        saved = await run_in_threadpool(save_png, request.app.state.layout.data, name, body)
    except TooBig as error:
        raise HTTPException(413, str(error)) from error
    except Invalid as error:
        raise HTTPException(400, str(error)) from error

    return {"upload": saved}
