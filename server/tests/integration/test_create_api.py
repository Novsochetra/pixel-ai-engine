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


def write_run(data, name: str, task: str, model: str | None = None) -> None:
    folder = data / "runs" / name
    (folder / "final").mkdir(parents=True)
    (folder / "final" / "pytorch_lora_weights.safetensors").write_bytes(b"")
    settings = {"task": task} | ({"model": model} if model else {})
    (folder / "run.json").write_text(json.dumps({"settings": settings, "created_at": "2026-11-20"}))


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


def test_a_side_view_draws_with_a_create_lora_that_learnt_sides(client, jobs, studio_data):
    run = studio_data / "runs" / "create-v1" / "run.json"
    run.write_text(json.dumps({"settings": {"task": "create", "views": ["front", "side"]}, "created_at": "2026-11-28"}))
    body = {"prompt": "a knight", "facing": "side", "drawWith": "runs/create-v1/final"}

    assert client.post("/api/generate", json=body, headers=SAME_SITE).status_code == 200
    args = started_args(jobs)
    assert args[args.index("--create-lora") + 1].endswith("runs/create-v1/final")
    assert args[-2:] == ["--facing", "side"]


@pytest.mark.parametrize(("body", "message"), [
    ({"prompt": ""}, "Write what to draw, in at most 1,000 characters."),
    ({"prompt": "a frog", "characters": 9}, "Characters must be a whole number from 1 to 8."),
    ({"prompt": "a frog", "drawWith": "runs/create-v1/final", "pose": "flying"}, "A create LoRA draws only standing"),
    ({"prompt": "a frog", "drawWith": "runs/create-v1/final", "facing": "side"}, "This create LoRA learnt no side"),
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

    assert rotate == [{"value": "runs/rotate-v2/final", "label": "rotate-v2 · final", "model": "flux2-klein-base-4b"}]
    assert create == [{"value": "runs/create-v1/final", "label": "create-v1 · final", "model": "flux2-klein-base-4b",
                       "views": ["front"]}]
    assert client.get("/api/loras", params={"task": "paint"}).status_code == 422


def test_a_create_lora_names_the_views_it_learnt(client, studio_data):
    write_run(studio_data, "pixie-draw-v1", "create")
    run = studio_data / "runs" / "pixie-draw-v1" / "run.json"
    run.write_text(json.dumps({"settings": {"task": "create", "views": ["front", "side"]}, "created_at": "2026-11-28"}))

    create = client.get("/api/loras", params={"task": "create"}).json()["loras"]

    assert {lora["value"]: lora["views"] for lora in create} == {
        "runs/pixie-draw-v1/final": ["front", "side"],
        "runs/create-v1/final": ["front"],
    }


def test_a_lora_names_the_model_it_was_trained_on(client, studio_data):
    write_run(studio_data, "rotate-fast", "rotate", model="flux2-klein-4b")

    rotate = client.get("/api/loras", params={"task": "rotate"}).json()["loras"]

    assert {lora["value"]: lora["model"] for lora in rotate} == {
        "runs/rotate-v2/final": "flux2-klein-base-4b",
        "runs/rotate-fast/final": "flux2-klein-4b",
    }


def test_the_form_options_are_listed(client):
    options = client.get("/api/generate/options").json()

    assert options["defaults"] == {"sprite": "128", "model": "flux2-klein-4b", "facing": "front"}
    assert options["characters"] == {"min": 1, "max": 8, "default": 2}


def test_an_uploaded_reference_goes_to_the_job(client, jobs, studio_data):
    save_png(studio_data / "uploads" / "20261127-hero.png")
    body = {"prompt": "a frog", "reference": "uploads/20261127-hero.png"}

    assert client.post("/api/generate", json=body, headers=SAME_SITE).status_code == 200
    assert started_args(jobs)[-2:] == ["--reference", str(studio_data.resolve() / "uploads/20261127-hero.png")]


def test_no_reference_adds_nothing(client, jobs):
    reply = client.post("/api/generate", json={"prompt": "a frog", "reference": ""}, headers=SAME_SITE)

    assert reply.status_code == 200
    assert "--reference" not in started_args(jobs)


@pytest.mark.parametrize("reference", ["uploads/missing.png", "generated/old-frog/s0-sheet.png", "../secret.png", 3])
def test_a_reference_must_be_an_upload(client, jobs, reference):
    reply = client.post("/api/generate", json={"prompt": "a frog", "reference": reference}, headers=SAME_SITE)

    assert reply.status_code == 400
    assert reply.json()["detail"] == "Pick a reference picture from your uploads."
    assert jobs.all() == []


def test_the_uploads_are_listed_newest_first(client, studio_data):
    save_png(studio_data / "uploads" / "20261126-old.png")
    save_png(studio_data / "uploads" / "20261127-new.png")

    uploads = client.get("/api/uploads").json()["uploads"]

    assert [upload["value"] for upload in uploads] == ["uploads/20261127-new.png", "uploads/20261126-old.png"]
    assert uploads[0]["src"] == "/api/files/uploads/20261127-new.png"


def test_the_form_options_have_the_upload_limits(client):
    options = client.get("/api/generate/options").json()

    assert options["largestUpload"] == 2048
    assert options["uploadLimit"] == 10_000_000
