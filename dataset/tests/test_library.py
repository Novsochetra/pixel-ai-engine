import json
import sqlite3

import pytest
from helpers import fake_lpc_4view, fake_pac

from pixel_data.analyze.run import analyze
from pixel_data.dashboard import exports, flagged, library, tryouts
from pixel_data.dashboard.library import Filters, open_db, view_label, warm_up
from pixel_data.export.run import export
from pixel_data.gather.importer import import_source
from pixel_data.sources import Layout


@pytest.fixture
def layout(tmp_path):
    layout = Layout(tmp_path)
    import_source(fake_pac(layout), layout)
    import_source(fake_lpc_4view(layout), layout)

    return layout


@pytest.fixture
def analyzed(tmp_path):
    layout = Layout(tmp_path)
    import_source(fake_pac(layout), layout)
    analyze(layout, [])

    return layout


def test_each_imported_source_is_summed_up(layout):
    with open_db(layout) as db:
        entries = {entry["source"]: entry for entry in library.imports(db)}

    assert entries["pac"]["characters"] == 3 and entries["lpc-4view"]["characters"] == 1
    assert list(entries["lpc-4view"]["views"]) == ["front", "left", "back", "right"]


def test_characters_can_be_filtered_by_source_split_and_search(layout):
    with open_db(layout) as db:
        _, every = library.character_page(db, Filters())
        tests, _ = library.character_page(db, Filters(source="pac", split="test"))
        spear, _ = library.character_page(db, Filters(search="spear"))

    assert every == 4
    assert [row["character"] for row in tests] == ["pac/test/0"]
    assert [row["character"] for row in spear] == ["lpc-4view/char_00000"]


def test_a_character_shows_every_view_in_order(layout):
    with open_db(layout) as db:
        images = library.character_images(db, "lpc-4view/char_00000")
        row = library.image_row(db, images[0]["id"])

    assert [image["view"] for image in images] == ["front", "left", "back", "right"]
    assert row["character"] == "lpc-4view/char_00000"


def test_the_records_open_read_only(layout):
    with open_db(layout) as db, pytest.raises(sqlite3.OperationalError):
        db.execute("DELETE FROM images")


def test_a_view_is_named_by_its_action_then_direction_or_its_size():
    assert view_label({"view": "left", "action": "walk", "width": 64}) == "walk · left"
    assert view_label({"view": "front", "width": 64}) == "front"
    assert view_label({"view": None, "width": 256}) == "256px"


def test_nothing_is_flagged_until_analysis_has_run(layout):
    warm_up(layout)

    with open_db(layout) as db:
        assert not flagged.analyzed(db)
        assert flagged.character_analysis(db, "pac/train/0") == ({}, None)


def test_flagged_images_are_counted_and_listed_by_flag(analyzed):
    warm_up(analyzed)

    with open_db(analyzed) as db:
        counts = flagged.flag_counts(db, "")
        images = flagged.flagged_images(db, "duplicate", "", 1)
        statuses = flagged.status_counts(db)

    assert counts["duplicate"] == 4
    assert "pac/train/0/front" in [image["id"] for image in images]
    assert statuses["pac"]["drop"] > 0


def test_a_copied_character_names_its_original(analyzed):
    with open_db(analyzed) as db:
        analysis, group = flagged.character_analysis(db, "pac/train/0")

    assert group["copy_of"] == "pac/test/0"
    assert "pac/train/0/front" in analysis


def test_an_export_is_read_with_the_same_samples_each_time(tmp_path):
    layout = Layout(tmp_path)
    pac = fake_pac(layout)
    import_source(pac, layout)
    analyze(layout, [])
    export(layout, [pac], "rotation-test", include_check=True, experimental=False)
    folder = layout.data / "exports"

    summaries = exports.read_exports(folder)

    assert [summary["name"] for summary in summaries] == ["rotation-test"]
    assert "leaks" in summaries[0]
    assert exports.samples(folder, "rotation-test") == exports.samples(folder, "rotation-test")


# opengameart-v1 keeps no left_out or leaks, and the whole exports page fell over on it.
def test_an_export_without_a_leak_check_is_still_read(tmp_path):
    folder = tmp_path / "exports" / "opengameart-v1"
    folder.mkdir(parents=True)
    summary = {"name": "opengameart-v1", "created_at": "2026-11-24T03:48:36+00:00",
               "sources": {"opengameart-2d": {"license": "CC0"}}, "characters": {"train": {"opengameart-2d": 1}}}
    (folder / "export.json").write_text(json.dumps(summary))
    entry = {"character": "opengameart-2d/0", "split": "train", "views": {"front": "images/front.png"}}
    (folder / "characters.jsonl").write_text(json.dumps(entry) + "\n")

    summaries = exports.read_exports(tmp_path / "exports")

    assert summaries[0]["name"] == "opengameart-v1" and "leaks" not in summaries[0]
    assert exports.samples(tmp_path / "exports", "opengameart-v1")["train"] == [entry]


def test_tryouts_are_read_newest_first_with_their_finished_models(tmp_path):
    for name, when in (("run-1", "2026-11-18T10:00:00+00:00"), ("run-2", "2026-11-19T10:00:00+00:00")):
        folder = tmp_path / "tryouts" / name
        folder.mkdir(parents=True)
        models = {"model-a": {"create": {}, "rotate": {}}, "model-b": {"error": "OSError: 401 gated"}}
        (folder / "results.json").write_text(json.dumps({"name": name, "created_at": when, "models": models}))

    runs = tryouts.read_runs(tmp_path / "tryouts")

    assert [run["name"] for run in runs] == ["run-2", "run-1"]
    assert tryouts.finished_models(runs[0]) == ["model-a"]
    assert tryouts.read_runs(tmp_path / "none") == []
