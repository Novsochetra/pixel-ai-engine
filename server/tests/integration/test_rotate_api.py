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
LORA = "runs/rotate-v2/final"


def write_run(data, name: str, task: str) -> None:
    folder = data / "runs" / name
    (folder / "final").mkdir(parents=True)
    (folder / "final" / "pytorch_lora_weights.safetensors").write_bytes(b"")
    (folder / "run.json").write_text(json.dumps({"settings": {"task": task}, "created_at": "2026-11-20"}))


def write_character(data, folder: str, views: list[str], info: dict) -> None:
    for view in views:
        save_png(data / "generated" / folder / f"s0-{view}.png")

    (data / "generated" / folder / "generated.json").write_text(json.dumps(info))


@pytest.fixture
def rotate_data(tmp_path):
    write_run(tmp_path, "rotate-v2", "rotate")
    write_run(tmp_path, "create-v1", "create")
    write_character(tmp_path, "frog", ["front"], {"prompt": "a frog", "created_at": "2026-11-21T04:00:00"})
    write_character(tmp_path, "knight", ["front", "left", "back", "right"],
                    {"prompt": "a knight", "created_at": "2026-11-22T04:00:00", "lora": "../data/runs/rotate-v2/final"})
    write_character(tmp_path, "turned-frog", ["front", "back"],
                    {"prompt": "a frog", "created_at": "2026-11-25T04:00:00", "lora": "/d/runs/rotate-v2/final",
                     "turn_model": "flux2-klein-4b", "sprite": 128, "rotated_from": "/d/generated/frog"})
    save_png(tmp_path / "uploads" / "20261125-100000-slime.png")

    return tmp_path


@pytest.fixture
def jobs(rotate_data):
    runner = Jobs(rotate_data / "jobs", rotate_data, command=[sys.executable, "-c", FAKE_JOB], cwd=rotate_data)
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


def test_a_good_form_starts_a_rotate_job(client, jobs, rotate_data):
    body = {"source": "generated/frog/s0", "lora": LORA, "turningModel": "flux2-klein-base-4b", "sprite": "96",
            "views": ["back", "left"]}

    reply = client.post("/api/rotate", json=body, headers=SAME_SITE)

    assert reply.status_code == 200
    assert reply.json()["job"]["title"] == "Rotate frog s0: 2 views"
    assert jobs.all()[0]["kind"] == "rotate"
    assert started_args(jobs) == ["rotate", str((rotate_data / "generated" / "frog").resolve()), "--seeds", "0",
                                  "--lora", str(rotate_data.resolve() / LORA), "--turn-model", "flux2-klein-base-4b",
                                  "--sprite", "96", "--views", "left", "back"]


def test_an_upload_is_turned(client, jobs, rotate_data):
    body = {"source": "uploads/20261125-100000-slime.png", "lora": LORA}

    assert client.post("/api/rotate", json=body, headers=SAME_SITE).status_code == 200
    assert started_args(jobs)[1] == str((rotate_data / "uploads" / "20261125-100000-slime.png").resolve())


@pytest.mark.parametrize(("body", "message"), [
    ({"source": "generated/frog/s0"}, "Pick a rotate LoRA from the list."),
    ({"source": "generated/frog/s0", "lora": "runs/create-v1/final"}, "Pick a rotate LoRA from the list."),
    ({"source": "generated/nobody/s0", "lora": LORA}, "Pick a character from the list."),
    ({"source": "generated/frog/s0", "lora": LORA, "views": []}, "Pick at least one view"),
    ({"source": "generated/frog/s0", "lora": LORA, "views": "back"}, "views must be a list"),
    ({"source": "generated/frog/s0", "lora": LORA, "sprite": 128}, "sprite must be text."),
])
def test_a_bad_form_says_what_is_wrong(client, jobs, body, message):
    reply = client.post("/api/rotate", json=body, headers=SAME_SITE)

    assert reply.status_code == 400
    assert reply.json()["detail"].startswith(message)
    assert jobs.all() == []


def test_a_second_job_waits_for_the_first(client):
    body = {"source": "generated/frog/s0", "lora": LORA}
    assert client.post("/api/rotate", json=body, headers=SAME_SITE).status_code == 200

    reply = client.post("/api/rotate", json=body, headers=SAME_SITE)

    assert reply.status_code == 409
    assert reply.json()["detail"] == "Another job is running. Wait for it, or stop it first."


def test_another_site_cannot_rotate(client, jobs):
    body = {"source": "generated/frog/s0", "lora": LORA}

    assert client.post("/api/rotate", json=body, headers={"sec-fetch-site": "cross-site"}).status_code == 403
    assert jobs.all() == []


def test_the_turned_characters_are_listed_newest_first(client):
    characters = client.get("/api/rotated").json()["characters"]

    assert [character["key"] for character in characters] == ["turned-frog/s0", "knight/s0"]
    assert characters[0]["rotatedFrom"] == "frog"
    assert characters[0]["turnWith"] == "rotate-v2 · final"
    assert [view["label"] for view in characters[1]["views"]] == ["Front", "Left", "Back", "Right"]
    assert client.get(characters[0]["views"][1]["src"]).headers["content-type"] == "image/png"


def test_the_choices_come_from_the_shared_constants(client):
    options = client.get("/api/rotate/options").json()

    assert options["views"] == ["left", "back", "right"]
    assert [model["value"] for model in options["models"]] == ["flux2-klein-4b", "flux2-klein-base-4b"]
    assert options["defaults"] == {"sprite": "128", "model": "flux2-klein-4b", "views": ["left", "back", "right"]}
