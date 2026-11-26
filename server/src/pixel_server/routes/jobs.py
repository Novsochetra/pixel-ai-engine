from fastapi import APIRouter, Request

from pixel_server.job_view import job_view

router = APIRouter()


def latest_view(request: Request) -> dict:
    jobs = request.app.state.jobs
    job = jobs.latest()

    return job_view(job, jobs.log(job["id"]) if job else "")


@router.get("/api/jobs/current")
def current_job(request: Request) -> dict:
    return latest_view(request)


# A plain def, so FastAPI runs it on a worker thread: stopping waits up to 20 s for the job to exit.
@router.post("/api/jobs/stop")
def stop_job(request: Request) -> dict:
    request.app.state.jobs.stop()

    return latest_view(request)
