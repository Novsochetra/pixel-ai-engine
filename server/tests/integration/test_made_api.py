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


def write_generated(data, folder: str) -> None:
    save_png(data / "generated" / folder / "s0-sheet.png")
    info = {"prompt": folder, "created_at": "2026-11-24T08:30:08+00:00"}
    (data / "generated" / folder / "generated.json").write_text(json.dumps(info))


@pytest.fixture
def jobs(tmp_path):
    write_generated(tmp_path, "frog")
    write_generated(tmp_path, "dragon")
    runner = Jobs(tmp_path / "jobs", tmp_path, command=[sys.executable, "-c", FAKE_JOB], cwd=tmp_path)
    yield runner
    runner.stop()


@pytest.fixture
def client(jobs):
    return TestClient(create_app(jobs))


def folders(client) -> list[str]:
    return [item["folder"] for item in client.get("/api/generated").json()["items"]]


def post(client, path: str, body: dict, headers: dict = SAME_SITE):
    return client.post(f"/api/generated/{path}", json=body, headers=headers)


def test_deleted_characters_leave_the_gallery_and_undo_brings_them_back(client):
    moved = post(client, "trash", {"folder": "frog"}).json()

    assert moved == {"folder": "frog", "trashed": "frog"}
    assert folders(client) == ["dragon"]

    assert post(client, "restore", moved).status_code == 200
    assert sorted(folders(client)) == ["dragon", "frog"]


@pytest.mark.parametrize(
    ("body", "status"),
    [({"folder": "../jobs"}, 400), ({}, 400), ({"folder": "ghost"}, 404)],
)
def test_a_bad_or_missing_folder_is_refused(client, body, status):
    assert post(client, "trash", body).status_code == status
    assert sorted(folders(client)) == ["dragon", "frog"]


def test_characters_a_running_job_uses_cannot_be_deleted(client, jobs, tmp_path):
    jobs.start("animate", "Animate frog", ["animate", str(tmp_path / "generated" / "frog")])
    deadline = time.monotonic() + 5
    while jobs.current() is None and time.monotonic() < deadline:
        time.sleep(0.05)

    reply = post(client, "trash", {"folder": "frog"})

    assert reply.status_code == 409
    assert "running job" in reply.json()["detail"]


def test_another_site_cannot_delete(client):
    reply = post(client, "trash", {"folder": "frog"}, {"sec-fetch-site": "cross-site"})

    assert reply.status_code == 403
    assert sorted(folders(client)) == ["dragon", "frog"]
