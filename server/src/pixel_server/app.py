from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pixel_data.dashboard.jobs import Jobs
from pixel_data.sources import Layout

from pixel_server.routes import (
    animate,
    characters,
    collections,
    create,
    flagged,
    health,
    jobs,
    pictures,
    training,
)
from pixel_server.same_site import is_same_site
from pixel_server.ui_files import UiFiles


def create_app(job_runner: Jobs, ui_dist: Path | None = None) -> FastAPI:
    app = FastAPI(title="Pixel Engine", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.jobs = job_runner
    app.state.layout = Layout(job_runner.data)

    @app.middleware("http")
    async def refuse_other_sites(request: Request, call_next):
        if not is_same_site(request.method, dict(request.headers)):
            return JSONResponse({"detail": "Only this dashboard can do that."}, status_code=403)

        return await call_next(request)

    for routes in (health, jobs, characters, flagged, collections, create, animate, training, pictures):
        app.include_router(routes.router)

    if ui_dist and (ui_dist / "index.html").exists():
        app.mount("/", UiFiles(directory=ui_dist, html=True), name="ui")

    return app
