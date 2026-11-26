import io
import json
import sys
import time

import pytest
from conftest import save_png
from fastapi.testclient import TestClient
from PIL import Image
from pixel_data.dashboard.jobs import Jobs

from pixel_server.app import create_app

SAME_SITE = {"sec-fetch-site": "same-origin"}
FAKE_JOB = "import time; time.sleep(30)"
PNG = {**SAME_SITE, "content-type": "image/png"}
CLIP = {"id": "s0-right-walk", "seed": 0, "frames": 33, "used": 29, "kept": 8}


def png_bytes(size: int = 16, kind: str = "PNG") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (size, size), (200, 40, 40)).save(buffer, kind)

    return buffer.getvalue()


def write_animated(data, folder: str, info: dict) -> None:
    run = data / "animated" / folder
    for clip in info["clips"]:
        save_png(run / f"{clip['id']}-sheet.png", size=32)
        for suffix in (".gif", "-raw.gif"):
            Image.new("RGB", (8, 8)).save(run / f"{clip['id']}{suffix}")

    (run / "animated.json").write_text(json.dumps(info))


@pytest.fixture
def animate_data(tmp_path):
    knight = tmp_path / "generated" / "knight"
    for view in ("front", "right"):
        save_png(knight / f"s0-{view}.png")
    save_png(knight / "s1-front.png")
    (knight / "generated.json").write_text(json.dumps({"prompt": "a knight", "created_at": "2026-11-24T08:00:00"}))
    save_png(tmp_path / "uploads" / "20261125-100000-slime.png")
    write_animated(tmp_path, "old-run", {"created_at": "2026-11-24T03:00:00", "source": "/x/knight", "clips": [CLIP]})
    write_animated(tmp_path, "new-run", {"created_at": "2026-11-25T03:00:00", "subject": "a slime", "same_end": False,
                                         "size": 384, "frames": 17, "clips": [{**CLIP, "id": "s0-hops"}]})

    return tmp_path


@pytest.fixture
def jobs(animate_data):
    runner = Jobs(animate_data / "jobs", animate_data, command=[sys.executable, "-c", FAKE_JOB], cwd=animate_data)
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


def test_a_good_form_starts_an_animate_job(client, jobs, animate_data):
    body = {"source": "generated/knight/s0", "views": ["front", "right"], "actions": "walk\n idle  \nwalk",
            "size": "512", "frames": "17", "subject": "a knight,  empty hands"}

    reply = client.post("/api/animate", json=body, headers=SAME_SITE)

    assert reply.status_code == 200
    assert reply.json()["job"]["title"] == "Animate knight: 4 clips"
    args = started_args(jobs)
    assert args[:7] == ["animate", str((animate_data / "generated" / "knight").resolve()), "--views", "front", "right",
                        "--seeds", "0"]
    assert args[7:13] == ["--actions", "walk", "idle", "--size", "512", "--frames"]
    assert args[-2:] == ["--subject", "a knight, empty hands"]


def test_an_uploaded_picture_is_animated_once(client, jobs, animate_data):
    body = {"source": "uploads/20261125-100000-slime.png", "actions": "hops", "subject": "a green slime"}

    assert client.post("/api/animate", json=body, headers=SAME_SITE).status_code == 200
    assert started_args(jobs)[1:4] == [str((animate_data / "uploads/20261125-100000-slime.png").resolve()),
                                       "--seeds", "0"]


@pytest.mark.parametrize(("body", "message"), [
    ({"source": "generated/knight/s0", "views": ["front"], "actions": ""}, "Say at least one action"),
    ({"source": "generated/knight/s1", "views": ["back"], "actions": "walk"}, "Pick at least one view that s1 has"),
    ({"source": "generated/nobody/s0", "views": ["front"], "actions": "walk"}, "Pick a character from the list."),
    ({"source": "uploads/missing.png", "actions": "walk", "subject": "a cat"}, "Pick a uploaded picture"),
    ({"source": "upload", "actions": "walk", "subject": "a cat"}, "Choose a PNG to upload."),
    ({"source": "generated/knight/s0", "views": "front", "actions": "walk"}, "views must be a list"),
    ({"source": "generated/knight/s0", "views": ["front"], "actions": ["walk"]}, "actions must be text."),
])
def test_a_bad_form_says_what_is_wrong(client, jobs, body, message):
    reply = client.post("/api/animate", json=body, headers=SAME_SITE)

    assert reply.status_code == 400
    assert reply.json()["detail"].startswith(message)
    assert jobs.all() == []


def test_a_second_job_waits_for_the_first(client):
    body = {"source": "generated/knight/s0", "views": ["front"], "actions": "walk"}
    assert client.post("/api/animate", json=body, headers=SAME_SITE).status_code == 200

    reply = client.post("/api/animate", json=body, headers=SAME_SITE)

    assert reply.status_code == 409
    assert reply.json()["detail"] == "Another job is running. Wait for it, or stop it first."


def test_another_site_cannot_animate_or_upload(client, jobs, animate_data):
    cross = {"sec-fetch-site": "cross-site"}
    body = {"source": "generated/knight/s0", "views": ["front"], "actions": "walk"}

    assert client.post("/api/animate", json=body, headers=cross).status_code == 403
    assert client.post("/api/uploads", content=png_bytes(), headers={**PNG, **cross}).status_code == 403
    assert jobs.all() == []
    assert len(list((animate_data / "uploads").iterdir())) == 1


def test_a_png_is_uploaded_and_listed(client, animate_data):
    reply = client.post("/api/uploads", params={"name": "My Slime!.png"}, content=png_bytes(), headers=PNG)

    upload = reply.json()["upload"]
    assert upload["value"].endswith("-my-slime.png")
    assert client.get(upload["src"]).headers["content-type"] == "image/png"
    assert upload in client.get("/api/animate/sources").json()["uploads"]


@pytest.mark.parametrize(("body", "kind", "status"), [
    (png_bytes(kind="JPEG"), "image/png", 400),
    (b"not a picture", "image/png", 400),
    (png_bytes(), "image/jpeg", 415),
    (png_bytes(4000), "image/png", 400),
    (b"\x89PNG\r\n\x1a\n" + bytes(10_000_001), "image/png", 413),
])
def test_a_bad_upload_is_refused(client, body, kind, status):
    reply = client.post("/api/uploads", content=body, headers={**SAME_SITE, "content-type": kind})

    assert reply.status_code == status
    assert len(client.get("/api/animate/sources").json()["uploads"]) == 1


def test_the_runs_are_listed_newest_first(client):
    runs = client.get("/api/animated").json()["runs"]

    assert [run["folder"] for run in runs] == ["new-run", "old-run"]
    assert runs[0]["openEnd"] is True
    assert runs[1]["clips"][0]["view"] == "right"
    assert client.get(runs[1]["clips"][0]["gif"]).headers["content-type"] == "image/gif"
    assert client.get(runs[1]["clips"][0]["sheet"]).headers["content-type"] == "image/png"


def test_only_pictures_in_animated_and_uploads_are_served(client):
    assert client.get("/api/files/animated/old-run/animated.json").status_code == 404
    assert client.get("/api/files/uploads/../generated/knight/generated.json").status_code == 404
    assert client.get("/api/files/uploads/%2e%2e/%2e%2e/etc/hosts").status_code == 404
    assert client.get("/api/files/generated/knight/s0-front.gif").status_code == 404
    assert client.get("/api/files/jobs/anything.png").status_code == 404


def test_the_characters_and_choices_are_listed(client):
    sources = client.get("/api/animate/sources").json()
    options = client.get("/api/animate/options").json()

    assert [made["value"] for made in sources["characters"]] == ["generated/knight/s0", "generated/knight/s1"]
    assert sources["characters"][0]["views"] == ["front", "right"]
    assert sources["characters"][0]["pictures"]["right"] == "/api/files/generated/knight/s0-right.png"
    assert options["views"] == ["front", "left", "back", "right"]
    assert options["mostActions"] == 8
