import sys
import time

import pytest
from fastapi.testclient import TestClient
from pixel_data.dashboard.jobs import Jobs

from pixel_server.app import create_app

FAKE_JOB = "import time; print(' 50%|█████     | 1/2', flush=True); time.sleep(30)"
FAKE_TRAINING = "import time; print('step 3/12: loss 0.2, 1.0% of the data', flush=True); time.sleep(30)"


@pytest.fixture
def jobs(tmp_path):
    runner = Jobs(tmp_path / "jobs", tmp_path, command=[sys.executable, "-c", FAKE_JOB], cwd=tmp_path)
    yield runner
    runner.stop()


@pytest.fixture
def client(jobs):
    return TestClient(create_app(jobs))


def wait_for_progress(client) -> dict:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        view = client.get("/api/jobs/current").json()
        if view["progress"] is not None:
            return view

        time.sleep(0.1)

    raise AssertionError("the job never wrote its progress")


def test_health_says_the_version(client):
    reply = client.get("/api/health").json()

    assert reply["ok"] is True
    assert reply["version"]


def test_no_job_yet(client):
    assert client.get("/api/jobs/current").json()["job"] is None


def test_running_job_shows_progress_and_stops(client, jobs):
    jobs.start("generate", "Make a dragon", [])

    view = wait_for_progress(client)
    assert view["job"]["status"] == "running"
    assert view["progress"] == 0.5

    stopped = client.post("/api/jobs/stop", headers={"sec-fetch-site": "same-origin"}).json()
    assert stopped["job"]["status"] in ("running", "stopped")


def test_training_job_shows_its_steps_as_progress(tmp_path):
    runner = Jobs(tmp_path / "jobs", tmp_path, command=[sys.executable, "-c", FAKE_TRAINING], cwd=tmp_path)
    runner.start("train", "Train rotate-v3", [])

    try:
        view = wait_for_progress(TestClient(create_app(runner)))
    finally:
        runner.stop()

    assert view["progress"] == 0.25
    assert view["step"].startswith("step 3/12")


def test_another_site_cannot_stop_a_job(client, jobs):
    jobs.start("generate", "Make a dragon", [])

    reply = client.post("/api/jobs/stop", headers={"sec-fetch-site": "cross-site"})

    assert reply.status_code == 403
    assert client.get("/api/jobs/current").json()["job"]["status"] == "running"


def test_built_ui_is_served_for_every_screen(jobs, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<div id=root></div>")
    client = TestClient(create_app(jobs, dist))

    assert client.get("/library").text == "<div id=root></div>"
    assert client.get("/api/missing").status_code == 404
