import json
import sys
import time

import pytest
from conftest import save_png
from fastapi.testclient import TestClient
from pixel_data.dashboard.jobs import Jobs

from pixel_server.app import create_app

SAME_SITE = {"sec-fetch-site": "same-origin"}
FAKE_JOB = "import time; time.sleep(30)"


def write_run(data, name: str, task: str) -> None:
    folder = data / "runs" / name
    (folder / "final").mkdir(parents=True)
    (folder / "final" / "pytorch_lora_weights.safetensors").write_bytes(b"")
    (folder / "run.json").write_text(json.dumps({"settings": {"task": task}, "created_at": "2026-11-20"}))


def write_generated(data, folder: str, info: dict) -> None:
    save_png(data / "generated" / folder / "s0-sheet.png")
    (data / "generated" / folder / "generated.json").write_text(json.dumps(info))


@pytest.fixture
def studio_data(tmp_path):
    write_run(tmp_path, "rotate-v2", "rotate")
    write_run(tmp_path, "create-v1", "create")
    write_generated(tmp_path, "old-frog", {"prompt": "a frog", "created_at": "2026-11-21T04:50:09+00:00"})
    write_generated(tmp_path, "new-dragon", {"prompt": "a dragon", "created_at": "2026-11-24T08:30:08+00:00",
                                             "sprite": 128, "facing": "side"})
    (tmp_path / "generated" / "drawing").mkdir()
    (tmp_path / "generated" / "drawing" / "generated.json").write_text("{}")

    return tmp_path


@pytest.fixture
def jobs(studio_data):
    runner = Jobs(studio_data / "jobs", studio_data, command=[sys.executable, "-c", FAKE_JOB], cwd=studio_data)
    yield runner
    runner.stop()


@pytest.fixture
def client(jobs):
    return TestClient(create_app(jobs))


def started_args(jobs) -> list[str]:
    deadline = time.monotonic() + 5
    while not jobs.all() and time.monotonic() < deadline:
        time.sleep(0.05)

    return jobs.all()[0]["args"]


def test_a_good_form_starts_a_generate_job(client, jobs, studio_data):
    body = {"prompt": "a frog  wizard", "characters": 3, "sprite": "96", "turnWith": "runs/rotate-v2/final"}

    reply = client.post("/api/generate", json=body, headers=SAME_SITE)

    assert reply.status_code == 200
    assert reply.json()["job"]["title"] == "Generate: a frog wizard"
    assert reply.json()["job"]["kind"] == "generate"
    assert started_args(jobs) == [
        "generate", "a frog wizard", "--seeds", "3", "--sprite", "96", "--turn-model", "flux2-klein-4b",
        "--front-model", "flux2-klein-4b", "--lora", str(studio_data.resolve() / "runs/rotate-v2/final"),
    ]


def test_a_side_view_is_drawn_and_not_turned(client, jobs):
    body = {"prompt": "a dragon", "pose": "flying", "facing": "side", "turnWith": "runs/rotate-v2/final"}

    assert client.post("/api/generate", json=body, headers=SAME_SITE).status_code == 200
    assert started_args(jobs)[-4:] == ["--pose", "flying", "--facing", "side"]


@pytest.mark.parametrize(("body", "message"), [
    ({"prompt": ""}, "Write what to draw, in at most 300 characters."),
    ({"prompt": "a frog", "characters": 9}, "Characters must be a whole number from 1 to 8."),
    ({"prompt": "a frog", "drawWith": "runs/create-v1/final", "pose": "flying"}, "A create LoRA draws only standing"),
    ({"prompt": "a frog", "turnWith": "runs/nothing/final"}, "Pick a trained model from the list."),
])
def test_a_bad_form_says_what_is_wrong(client, jobs, body, message):
    reply = client.post("/api/generate", json=body, headers=SAME_SITE)

    assert reply.status_code == 400
    assert reply.json()["detail"].startswith(message)
    assert jobs.all() == []


def test_a_second_job_waits_for_the_first(client):
    assert client.post("/api/generate", json={"prompt": "a frog"}, headers=SAME_SITE).status_code == 200

    reply = client.post("/api/generate", json={"prompt": "a toad"}, headers=SAME_SITE)

    assert reply.status_code == 409
    assert reply.json()["detail"] == "Another job is running. Wait for it, or stop it first."


def test_another_site_cannot_generate(client, jobs):
    reply = client.post("/api/generate", json={"prompt": "a frog"}, headers={"sec-fetch-site": "cross-site"})

    assert reply.status_code == 403
    assert jobs.all() == []


def test_the_made_characters_are_listed_newest_first(client):
    items = client.get("/api/generated").json()["items"]

    assert [item["folder"] for item in items] == ["new-dragon", "old-frog"]
    assert items[0]["sheets"][0]["src"] == "/api/files/generated/new-dragon/s0-sheet.png"
    assert client.get(items[0]["sheets"][0]["src"]).headers["content-type"] == "image/png"


def test_only_pictures_in_generated_are_served(client, studio_data):
    assert client.get("/api/files/generated/old-frog/generated.json").status_code == 404
    assert client.get("/api/files/generated/../runs/rotate-v2/run.json").status_code == 404
    assert client.get("/api/files/generated/%2e%2e/%2e%2e/etc/hosts").status_code == 404


def test_the_loras_are_listed_by_task(client):
    rotate = client.get("/api/loras", params={"task": "rotate"}).json()["loras"]
    create = client.get("/api/loras", params={"task": "create"}).json()["loras"]

    assert rotate == [{"value": "runs/rotate-v2/final", "label": "rotate-v2 · final"}]
    assert create == [{"value": "runs/create-v1/final", "label": "create-v1 · final"}]
    assert client.get("/api/loras", params={"task": "paint"}).status_code == 422


def test_the_form_options_are_listed(client):
    options = client.get("/api/generate/options").json()

    assert options["defaults"] == {"sprite": "128", "model": "flux2-klein-4b", "facing": "front"}
    assert options["characters"] == {"min": 1, "max": 8, "default": 2}
