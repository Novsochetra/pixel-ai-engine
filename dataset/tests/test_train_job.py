import json
from pathlib import Path

import pytest

from pixel_data.dashboard import studio
from pixel_data.dashboard.train_data import trainable_sources

FORM = {"name": "pixie-draw-v1", "task": "create", "export": "characters-v2-data", "model": "flux2-klein-base-4b",
        "size": "256", "steps": "500"}
CHARACTERS = ["lpc-4view", "pac", "pixellab"]


def write_export(data: Path, name: str, sources: dict, train: dict) -> None:
    export = data / "exports" / name
    export.mkdir(parents=True)
    (export / "characters.jsonl").write_text("")
    (export / "export.json").write_text(json.dumps({"sources": sources, "characters": {"train": train}}))


# characters-v2-data lists the licence of every source it read, but only three gave it characters.
@pytest.fixture
def data(tmp_path):
    licences = {name: {"license": "CC0", "use": "train"} for name in [*CHARACTERS, "atlas-1.4m", "moss-64"]}
    write_export(tmp_path, "characters-v2-data", licences, {"lpc-4view": 45016, "pac": 10898, "pixellab": 692})
    write_export(tmp_path, "opengameart-v1-data", {"opengameart-2d": {"license": "CC0"}}, {"opengameart-2d": 5188})

    return tmp_path


def test_only_sources_with_characters_to_train_on_count(data):
    assert trainable_sources(data, "characters-v2-data") == CHARACTERS


def test_a_new_run_on_every_character_source_names_none(data):
    _, args = studio.train_job(data, {**FORM, "sources_list": CHARACTERS})

    assert "--sources" not in args


def test_a_new_create_run_takes_more_exports_and_repeats(data):
    form = {**FORM, "sources_list": [*CHARACTERS, "opengameart-2d"], "more_exports": ["opengameart-v1-data"],
            "repeat": {"opengameart-2d": 5, "pixellab": 10, "pac": 1}}

    _, args = studio.train_job(data, form)

    assert args[args.index("--more-exports"):][:2] == ["--more-exports", "opengameart-v1-data"]
    assert "--sources" not in args
    assert args[args.index("--repeat"):] == ["--repeat", "opengameart-2d=5", "pixellab=10"]


@pytest.mark.parametrize("change", [
    {"task": "rotate", "more_exports": ["opengameart-v1-data"]},
    {"more_exports": ["characters-v2-data"]},
    {"more_exports": ["nowhere"]},
    {"repeat": {"atlas-1.4m": 2}},
    {"repeat": {"pac": 0}},
    {"repeat": {"pac": 21}},
    {"repeat": {"pac": "5"}},
])
def test_a_new_run_refuses_more_data_it_cannot_use(data, change):
    with pytest.raises(studio.Invalid):
        studio.train_job(data, {**FORM, "sources_list": CHARACTERS, **change})
