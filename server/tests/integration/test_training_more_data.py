import json
import sys
import time

import pytest
from fastapi.testclient import TestClient
from pixel_data.dashboard.jobs import Jobs
from training_data import training_data

from pixel_server.app import create_app

SAME_SITE = {"sec-fetch-site": "same-origin"}
NEW_RUN = {"name": "pixie-draw-v2", "task": "create", "export": "characters-v2-data", "model": "flux2-klein-base-4b",
           "size": "256", "steps": 500, "sources": ["lpc-4view", "pixellab", "opengameart-2d"],
           "moreExports": ["opengameart-v1-data"], "repeat": {"opengameart-2d": 5, "pixellab": 10}}


def write_export(data, name: str, sources: list[str], train: dict) -> None:
    export = data / "exports" / name
    export.mkdir(parents=True)
    (export / "characters.jsonl").write_text("")
    licences = {source: {"license": "CC0", "use": "train"} for source in sources}
    (export / "export.json").write_text(json.dumps({"sources": licences, "characters": {"train": train}}))


@pytest.fixture
def data(tmp_path):
    data = training_data(tmp_path)
    counts = {"lpc-4view": 45016, "pixellab": 692}
    write_export(data, "characters-v2-data", ["atlas-1.4m", "lpc-4view", "pixellab"], counts)
    write_export(data, "opengameart-v1-data", ["opengameart-2d"], {"opengameart-2d": 5188})

    return data


@pytest.fixture
def jobs(data):
    runner = Jobs(data / "jobs", data, command=[sys.executable, "-c", "import time; time.sleep(30)"], cwd=data)
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


def test_the_form_lists_only_sources_with_characters_and_how_many(client):
    exports = client.get("/api/training/options").json()["exports"]

    characters = next(entry for entry in exports if entry["name"] == "characters-v2-data")
    assert characters["sources"] == [
        {"name": "lpc-4view", "licence": "CC0", "use": "train", "count": 45016},
        {"name": "pixellab", "licence": "CC0", "use": "train", "count": 692},
    ]


def test_a_new_create_run_trains_on_more_exports_with_repeats(client, jobs):
    reply = client.post("/api/training/start", json=NEW_RUN, headers=SAME_SITE)

    assert reply.status_code == 200
    args = started(jobs)["args"]
    assert args[args.index("--more-exports"):][:2] == ["--more-exports", "opengameart-v1-data"]
    assert "--sources" not in args
    assert args[args.index("--repeat"):] == ["--repeat", "opengameart-2d=5", "pixellab=10"]


@pytest.mark.parametrize("change", [{"moreExports": "opengameart-v1-data"}, {"repeat": ["pixellab", 10]},
                                    {"repeat": {"pixellab": 99}}, {"task": "rotate"}])
def test_a_new_run_with_more_data_it_cannot_use_is_refused(client, change):
    reply = client.post("/api/training/start", json={**NEW_RUN, **change}, headers=SAME_SITE)

    assert reply.status_code == 400
