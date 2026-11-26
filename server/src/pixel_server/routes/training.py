from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request
from pixel_data.dashboard import studio

from pixel_server.routes.jobs import latest_view
from pixel_server.training.run_list import run_list
from pixel_server.training.training_form import resume_form, start_form, tryout_form
from pixel_server.training.training_options import training_options

router = APIRouter()

# The old pages started all three as "training" jobs; the job list keeps that name.
KIND = "training"


@router.get("/api/runs")
def runs(request: Request) -> dict:
    return run_list(request.app.state.layout.data, request.app.state.jobs.latest())


@router.get("/api/training/options")
def options(request: Request) -> dict:
    return training_options(request.app.state.layout.data)


def start(request: Request, make: Callable, old_form: Callable, body: dict) -> dict:
    try:
        title, args = make(request.app.state.layout.data, old_form(body))
        request.app.state.jobs.start(KIND, title, args)
    except studio.Invalid as error:
        raise HTTPException(400, str(error)) from error
    except RuntimeError as error:
        raise HTTPException(409, str(error)) from error

    return latest_view(request)


# Plain defs, so FastAPI runs them on a worker thread while the job's process starts.
@router.post("/api/training/start")
def start_training(request: Request, body: dict) -> dict:
    return start(request, studio.train_job, start_form, body)


@router.post("/api/training/resume")
def resume_training(request: Request, body: dict) -> dict:
    return start(request, studio.resume_job, resume_form, body)


@router.post("/api/training/tryout")
def try_out(request: Request, body: dict) -> dict:
    return start(request, studio.tryout_job, tryout_form, body)
