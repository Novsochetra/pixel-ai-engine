from fastapi import APIRouter, HTTPException, Request
from pixel_data.dashboard.rotate_job import rotate_job
from pixel_data.dashboard.studio import Invalid

from pixel_server.rotate.rotate_form import rotate_form
from pixel_server.rotate.rotate_options import rotate_options
from pixel_server.rotate.rotated_list import rotated_list
from pixel_server.routes.jobs import latest_view

router = APIRouter()


@router.get("/api/rotated")
def rotated(request: Request) -> dict:
    return rotated_list(request.app.state.layout.data)


@router.get("/api/rotate/options")
def options() -> dict:
    return rotate_options()


# A plain def, so FastAPI runs it on a worker thread while the job's process starts.
@router.post("/api/rotate")
def rotate(request: Request, body: dict) -> dict:
    try:
        title, args = rotate_job(request.app.state.layout.data, rotate_form(body))
        request.app.state.jobs.start("rotate", title, args)
    except Invalid as error:
        raise HTTPException(400, str(error)) from error
    except RuntimeError as error:
        raise HTTPException(409, str(error)) from error

    return latest_view(request)
