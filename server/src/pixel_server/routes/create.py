from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pixel_data.dashboard import studio

from pixel_server.create.form_options import form_options, lora_list
from pixel_server.create.generate_form import studio_form
from pixel_server.create.generated_list import generated_list
from pixel_server.routes.jobs import latest_view

router = APIRouter()


@router.get("/api/generated")
def generated(request: Request) -> dict:
    return generated_list(request.app.state.layout.data)


@router.get("/api/generate/options")
def options() -> dict:
    return form_options()


@router.get("/api/loras")
def loras(request: Request, task: Literal["create", "rotate"]) -> dict:
    return lora_list(request.app.state.layout.data, task)


# A plain def, so FastAPI runs it on a worker thread while the job's process starts.
@router.post("/api/generate")
def generate(request: Request, body: dict) -> dict:
    try:
        title, args = studio.generate_job(request.app.state.layout.data, studio_form(body))
        request.app.state.jobs.start("generate", title, args)
    except studio.Invalid as error:
        raise HTTPException(400, str(error)) from error
    except RuntimeError as error:
        raise HTTPException(409, str(error)) from error

    return latest_view(request)
