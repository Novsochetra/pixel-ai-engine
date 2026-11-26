import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pixel_data.analyze.run import analyze
from pixel_data.dashboard.jobs import Jobs
from pixel_data.records import Record, connect, log_import, replace_source
from pixel_data.sources import Layout

from pixel_server.app import create_app

VIEWS = ("front", "left", "back", "right")
EXPORT_SUMMARY = {
    "created_at": "2026-11-18T10:00:00+00:00",
    "characters": {"train": {"fake": 1}},
    "left_out": {"a view is dropped": 2},
    "leaks": {"groups_in_two_splits": 0},
}


def save_png(path, size: int = 16, color: tuple = (200, 40, 40, 255)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    image.paste(color, (2, 2, size - 2, size - 2))
    image.save(path)


def knight_records(layout: Layout) -> list[Record]:
    records = []
    for number, caption in ((0, "a knight with a spear"), (1, "a green frog")):
        for shade, view in enumerate(VIEWS):
            file = f"fake/{number}-{view}.png"
            save_png(layout.raw / file, color=(shade * 60, number * 90, 10, 255))
            records.append(
                Record(f"fake/{number}/{view}", "fake", f"fake/{number}", view, 16, 16, file, "CC0", "train",
                       caption=caption, source_split="train")
            )

    # Nothing drawn, so `pixel analyze` flags it as empty.
    Image.new("RGBA", (16, 16)).save(layout.raw / "fake/blank.png")
    records.append(Record("fake/2/front", "fake", "fake/2", "front", 16, 16, "fake/blank.png", "CC0", "train"))

    return records


def write_export(data, name: str, summary: dict) -> None:
    folder = data / "exports" / name
    save_png(folder / "images" / "front.png")
    (folder / "export.json").write_text(json.dumps({"name": name, "sources": {"fake": {"license": "CC0"}}, **summary}))
    entry = {"character": "fake/0", "split": "train", "views": {"front": "images/front.png"}}
    (folder / "characters.jsonl").write_text(json.dumps(entry) + "\n")


def write_tryout(data) -> None:
    folder = data / "tryouts" / "run-1"
    save_png(folder / "model-a" / "p00-s0-pixel.png")
    results = {
        "name": "run-1", "created_at": "2026-11-18T10:00:00+00:00", "device": "mps", "seeds": [0],
        "repos": {"model-a": "someone/model-a", "model-b": "someone/model-b"},
        "create": [{"id": "p00", "prompt": "pixel art of a knight"}],
        "rotate": [],
        "models": {
            "model-a": {"create": {"p00-s0": {"raw": None, "pixel": "model-a/p00-s0-pixel.png"}}, "rotate": {},
                        "load_seconds": 30.0, "seconds_per_image": 12.5},
            "model-b": {"error": "OSError: 401 gated"},
        },
    }
    (folder / "results.json").write_text(json.dumps(results))


@pytest.fixture
def library(tmp_path):
    layout = Layout(tmp_path)
    with connect(layout.records) as db:
        replace_source(db, "fake", knight_records(layout))
        log_import(db, "fake", {})

    analyze(layout, [])
    write_export(tmp_path, "rotation-test", EXPORT_SUMMARY)
    write_tryout(tmp_path)

    return layout


@pytest.fixture
def library_client(library):
    return TestClient(create_app(Jobs(library.data / "jobs", library.data)))
