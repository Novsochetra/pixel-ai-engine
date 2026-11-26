import json

import pytest
from helpers import png_bytes

from pixel_data.gather import pixellab
from pixel_data.gather.importer import import_source
from pixel_data.gather.pixellab import JOB_FILE, Refused, Stop, fetch_picture, gather_pixellab, read_token, to_make
from pixel_data.sources import Layout, Source

SOURCE = Source("pixellab", "pixellab", "PixelLab output", "hold", ["create", "rotate"], links=["https://example.com"])
DIRECTIONS = ("south", "west", "east", "north")


class FakeApi:
    def __init__(self, fail: set[str] = frozenset(), stop_after: int | None = None):
        self.created = []
        self.fail = fail
        self.stop_after = stop_after
        self.jobs_gone = False

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        if path == "/balance":
            return {"subscription": {"generations": 100, "total": 2000, "plan": "tier", "status": "active"}}

        if path == "/create-character-v3":
            if self.stop_after is not None and len(self.created) >= self.stop_after:
                raise Stop("no credits")
            if body["name"] in self.fail:
                raise Refused("422: bad description")

            self.created.append(body["name"])
            return {"background_job_id": f"job-{body['name']}", "character_id": body["name"]}

        if path.startswith("/background-jobs/"):
            if self.jobs_gone:
                raise Refused('404: {"detail":"Job not found"}')
            return {"status": "completed", "usage": {"type": "generations", "generations": 2}}

        name = path.rsplit("/", 1)[1]
        return {
            "size": {"width": 8, "height": 8},
            "view": "low top-down",
            "rotation_urls": {direction: f"https://supabase.pixellab.ai/{name}/{direction}.png" for direction in DIRECTIONS},
        }


def write_plan(tmp_path, count: int):
    plan = tmp_path / "plan.json"
    defaults = {"size": 64, "directions": 4, "view": "low top-down", "outline": "single color black outline", "detail": "medium detail"}
    characters = [{"id": f"c-{index:03}", "group": "c", "body": "blob", "description": f"a blob number {index}"} for index in range(count)]
    plan.write_text(json.dumps({"version": 1, "defaults": defaults, "characters": characters}))

    return plan


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(pixellab, "fetch_picture", lambda url: png_bytes(8))
    monkeypatch.setattr(pixellab.time, "sleep", lambda seconds: None)


def test_only_the_asked_number_is_made_and_a_second_run_goes_on(tmp_path):
    layout = Layout(tmp_path / "data")
    plan = write_plan(tmp_path, 5)
    api = FakeApi()

    first = gather_pixellab(SOURCE, layout, plan, tmp_path / ".env", limit=2, parallel=1, api=api)
    second = gather_pixellab(SOURCE, layout, plan, tmp_path / ".env", limit=2, parallel=1, api=api)

    assert first["made"] == 2 and second["made"] == 2
    assert api.created == ["c-000", "c-001", "c-002", "c-003"]


def test_skip_leaves_the_first_entries_to_another_run(tmp_path):
    layout = Layout(tmp_path / "data")
    api = FakeApi()

    gather_pixellab(SOURCE, layout, write_plan(tmp_path, 5), tmp_path / ".env", limit=5, parallel=1, api=api, skip=3)

    assert api.created == ["c-003", "c-004"]


def test_a_paid_job_is_finished_before_new_ones_start(tmp_path):
    folder = tmp_path / "c-004"
    folder.mkdir()
    (folder / JOB_FILE).write_text("{}")
    characters = [{"id": f"c-{index:03}"} for index in range(5)]

    assert [entry["id"] for entry in to_make(tmp_path, characters, 2)] == ["c-004", "c-000"]


def test_a_paid_character_is_saved_after_its_job_is_gone(tmp_path):
    layout = Layout(tmp_path / "data")
    folder = layout.source_dir(SOURCE) / "c-000"
    folder.mkdir(parents=True)
    (folder / JOB_FILE).write_text(json.dumps({"background_job_id": "job-c-000", "character_id": "c-000"}))
    api = FakeApi()
    api.jobs_gone = True

    summary = gather_pixellab(SOURCE, layout, write_plan(tmp_path, 1), tmp_path / ".env", limit=1, parallel=1, api=api)

    assert summary["made"] == 1 and api.created == []
    assert (folder / "character.json").is_file()


def test_a_refused_character_is_noted_and_the_rest_go_on(tmp_path):
    layout = Layout(tmp_path / "data")
    plan = write_plan(tmp_path, 3)

    summary = gather_pixellab(SOURCE, layout, plan, tmp_path / ".env", limit=3, parallel=1, api=FakeApi(fail={"c-001"}))

    assert summary["made"] == 2 and summary["failed"] == 1
    failed = (layout.source_dir(SOURCE) / "failed.jsonl").read_text()
    assert "c-001" in failed and "bad description" in failed


def test_no_credits_stops_every_call(tmp_path):
    layout = Layout(tmp_path / "data")
    plan = write_plan(tmp_path, 4)

    summary = gather_pixellab(SOURCE, layout, plan, tmp_path / ".env", limit=4, parallel=1, api=FakeApi(stop_after=1))

    assert summary["made"] == 1
    assert summary["stopped"] == "no credits"


def test_made_characters_import_as_held_records(tmp_path):
    layout = Layout(tmp_path / "data")
    gather_pixellab(SOURCE, layout, write_plan(tmp_path, 1), tmp_path / ".env", limit=1, parallel=1, api=FakeApi())

    entry = import_source(SOURCE, layout)

    assert entry["images"] == 4 and entry["characters"] == 1


def test_the_token_comes_from_the_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("PIXELLAB_SECRET", raising=False)
    env = tmp_path / ".env"

    with pytest.raises(SystemExit, match="No PixelLab token"):
        read_token(env)

    env.write_text("OTHER=1\nPIXELLAB_SECRET='abc123'\n")
    assert read_token(env) == "abc123"


def test_pictures_are_fetched_only_from_pixellab_hosts():
    with pytest.raises(Refused, match="unknown host"):
        fetch_picture("https://evil.example.com/x.png")

    with pytest.raises(Refused, match="unknown host"):
        fetch_picture("https://pixellab.ai.evil.example.com/x.png")
