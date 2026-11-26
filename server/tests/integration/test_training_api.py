import sys
import time

import pytest
from fastapi.testclient import TestClient
from pixel_data.dashboard.jobs import Jobs
from training_data import training_data

from pixel_server.app import create_app

SAME_SITE = {"sec-fetch-site": "same-origin"}
FAKE_JOB = "import time; time.sleep(30)"
NEW_RUN = {"name": "rotate-v3", "task": "rotate", "export": "rotation-v1", "model": "flux2-klein-base-4b",
           "size": "256", "steps": 400, "sources": ["pac"]}
TRYOUT = {"run": "rotate-v2", "checkpoint": "runs/rotate-v2/checkpoints/step-000010", "model": "flux2-klein-4b",
          "characters": 3}


@pytest.fixture
def data(tmp_path):
    return training_data(tmp_path)


@pytest.fixture
def jobs(data):
    runner = Jobs(data / "jobs", data, command=[sys.executable, "-c", FAKE_JOB], cwd=data)
    yield runner
    runner.stop()


@pytest.fixture
def client(jobs):
    return TestClient(create_app(jobs))


def started(jobs) -> dict:
    deadline = time.monotonic() + 5
    while not jobs.all() and time.monotonic() < deadline:
        time.sleep(0.05)

    return jobs.all()[0]


def test_a_new_run_starts_with_the_chosen_sources(client, jobs):
    reply = client.post("/api/training/start", json=NEW_RUN, headers=SAME_SITE)

    assert reply.status_code == 200
    assert reply.json()["job"]["title"] == "Train rotate-v3: 400 steps"
    job = started(jobs)
    assert job["kind"] == "training"
    assert job["args"] == ["train", "--name", "rotate-v3", "--task", "rotate", "--export", "rotation-v1", "--model",
                           "flux2-klein-base-4b", "--size", "256", "--steps", "400", "--sources", "pac"]


def test_a_new_run_on_every_source_names_none(client, jobs):
    body = {**NEW_RUN, "sources": ["pac", "lpc-4view"]}

    assert client.post("/api/training/start", json=body, headers=SAME_SITE).status_code == 200
    assert "--sources" not in started(jobs)["args"]


def test_a_resume_goes_on_with_the_runs_own_settings(client, jobs):
    reply = client.post("/api/training/resume", json={"run": "pixie-draw-v1", "steps": 510}, headers=SAME_SITE)

    assert reply.json()["job"]["title"] == "Resume pixie-draw-v1 to 510 steps"
    args = started(jobs)["args"]
    assert args[:7] == ["train", "--name", "pixie-draw-v1", "--resume", "--task", "create", "--steps"]
    assert args[-4:] == ["--more-exports", "opengameart-v1", "--repeat", "pac=5"]


def test_a_tryout_turns_test_characters_with_a_checkpoint(client, jobs, data):
    reply = client.post("/api/training/tryout", json=TRYOUT, headers=SAME_SITE)

    assert reply.json()["job"]["title"] == "Try rotate-v2 step-000010 on the fast model"
    args = started(jobs)["args"]
    assert args[:5] == ["tryout", "--models", "flux2-klein-4b", "--lora",
                        str(data.resolve() / "runs/rotate-v2/checkpoints/step-000010")]
    assert args[args.index("--rotate") + 1] == "3"


@pytest.mark.parametrize(("form", "message"), [
    (("start", {**NEW_RUN, "name": "rotate-v2"}), "There is already a run called rotate-v2."),
    (("start", {**NEW_RUN, "name": "bad name!"}), "The run name may have"),
    (("start", {**NEW_RUN, "sources": []}), "Pick at least one source."),
    (("start", {**NEW_RUN, "sources": "pac"}), "sources must be a list"),
    (("start", {**NEW_RUN, "export": "nowhere"}), "Pick a export from the list."),
    (("resume", {"run": "rotate-v2", "steps": 20}), "Steps must be a whole number from 21"),
    (("resume", {"run": "nobody", "steps": 40}), "No such run."),
    (("tryout", {**TRYOUT, "run": "pixie-draw-v1"}), "A create run is tried on the Generate page."),
    (("tryout", {**TRYOUT, "characters": 21}), "Test characters must be a whole number from 1 to 20."),
    (("tryout", {**TRYOUT, "checkpoint": "runs/pixie-draw-v1/checkpoints/step-000010"}), "Pick a checkpoint"),
])
def test_a_bad_form_says_what_is_wrong(client, jobs, form, message):
    path, body = form

    reply = client.post(f"/api/training/{path}", json=body, headers=SAME_SITE)

    assert reply.status_code == 400
    assert reply.json()["detail"].startswith(message)
    assert jobs.all() == []


def test_a_second_job_waits_for_the_first(client):
    assert client.post("/api/training/tryout", json=TRYOUT, headers=SAME_SITE).status_code == 200

    reply = client.post("/api/training/resume", json={"run": "rotate-v2", "steps": 40}, headers=SAME_SITE)

    assert reply.status_code == 409
    assert reply.json()["detail"] == "Another job is running. Wait for it, or stop it first."


@pytest.mark.parametrize("path", ["start", "resume", "tryout"])
def test_another_site_cannot_start_training(client, jobs, path):
    body = {"start": NEW_RUN, "resume": {"run": "rotate-v2", "steps": 40}, "tryout": TRYOUT}[path]

    reply = client.post(f"/api/training/{path}", json=body, headers={"sec-fetch-site": "cross-site"})

    assert reply.status_code == 403
    assert jobs.all() == []


def test_the_runs_are_listed_newest_first(client):
    runs = client.get("/api/runs").json()["runs"]

    assert [run["name"] for run in runs] == ["pixie-draw-v1", "rotate-v2"]
    assert runs[0]["passes"] == 0.1
    assert runs[0]["moreExports"] == ["opengameart-v1"]
    assert runs[1]["passes"] is None
    assert (runs[1]["step"], runs[1]["steps"], runs[1]["secondsPerStep"]) == (20, 20, 27.0)
    assert runs[1]["val"] == [[10, 0.15], [20, 0.12]]
    assert len(runs[1]["loss"]) == 20
    assert [choice["label"] for choice in runs[1]["tryouts"]] == ["final", "step-000010"]


def test_the_run_being_trained_says_so(client):
    client.post("/api/training/resume", json={"run": "rotate-v2", "steps": 40}, headers=SAME_SITE)

    runs = client.get("/api/runs").json()["runs"]

    assert [run["isTraining"] for run in runs] == [False, True]


def test_the_form_choices_list_each_export_and_its_licences(client):
    options = client.get("/api/training/options").json()

    assert options["exports"] == [{"name": "rotation-v1", "sources": [
        {"name": "lpc-4view", "licence": "CC-BY-SA-3.0", "use": "train"},
        {"name": "pac", "licence": "CC-BY-NC-4.0", "use": "train"},
    ]}]
    assert [task["value"] for task in options["tasks"]] == ["rotate", "create"]
    assert options["defaults"]["addSteps"] == 500
