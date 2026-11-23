import json

import pytest
from helpers import QUADRANT_COLORS, fake_icons, fake_landscapes, fake_lpc_4view, fake_lpc_action, fake_moss_64, fake_pac

from pixel_data.gather.importer import import_source
from pixel_data.images import load_image
from pixel_data.records import connect
from pixel_data.sources import Layout, Source


def rows(layout: Layout, source: str) -> list:
    db = connect(layout.records)
    try:
        return db.execute("SELECT * FROM images WHERE source = ? ORDER BY id", (source,)).fetchall()
    finally:
        db.close()


def test_pac_makes_one_record_per_view_and_keeps_splits_apart(tmp_path):
    layout = Layout(tmp_path)
    entry = import_source(fake_pac(layout), layout)

    assert (entry["images"], entry["characters"]) == (12, 3)
    assert json.loads(entry["skipped"]) == {"file is not <number>.<view>.png": 2}

    characters = {row["character"] for row in rows(layout, "pac")}
    assert characters == {"pac/train/0", "pac/train/1", "pac/test/0"}


def test_pac_records_load_back_the_exact_picture(tmp_path):
    layout = Layout(tmp_path)
    import_source(fake_pac(layout), layout)

    left = next(row for row in rows(layout, "pac") if row["id"] == "pac/train/1/left")
    image = load_image(layout.raw, left)

    assert image.size == (64, 64)
    assert image.getpixel((0, 0)) == (60, 90, 10, 255)


def test_lpc_sheets_are_cut_into_their_four_views(tmp_path):
    layout = Layout(tmp_path)
    entry = import_source(fake_lpc_4view(layout), layout)

    assert (entry["images"], entry["characters"]) == (4, 1)
    assert json.loads(entry["skipped"]) == {"sheet is not 128x128": 1}

    for row in rows(layout, "lpc-4view"):
        image = load_image(layout.raw, row)
        assert image.size == (64, 64)
        assert image.getpixel((32, 32)) == QUADRANT_COLORS[row["view"]]


def test_lpc_captions_drop_the_words_about_the_sheet(tmp_path):
    layout = Layout(tmp_path)
    import_source(fake_lpc_4view(layout), layout)

    captions = {row["caption"] for row in rows(layout, "lpc-4view")}

    assert captions == {"lpc-style pixel art character, with spear"}


def test_importing_again_replaces_only_that_source(tmp_path):
    layout = Layout(tmp_path)
    pac = fake_pac(layout)
    import_source(pac, layout)
    import_source(fake_lpc_4view(layout), layout)

    import_source(pac, layout)

    assert len(rows(layout, "pac")) == 12
    assert len(rows(layout, "lpc-4view")) == 4


def test_a_source_without_an_importer_says_which_ones_exist(tmp_path):
    layout = Layout(tmp_path)
    source = Source("atlas", "huggingface", "CC0", "train", ["create"])

    with pytest.raises(SystemExit, match="Importers so far: atlas-1.4m, icons-172k, landscapes-20k, lpc-4view"):
        import_source(source, layout)


def test_a_source_must_be_downloaded_before_import(tmp_path):
    layout = Layout(tmp_path)
    source = Source("pac", "huggingface", "CC-BY-NC-4.0", "train", ["rotate"])

    with pytest.raises(SystemExit, match="Run `pixel gather pac` first"):
        import_source(source, layout)


def test_lpc_action_sheets_become_one_strip_per_action_and_direction(tmp_path):
    layout = Layout(tmp_path)
    entry = import_source(fake_lpc_action(layout), layout)

    assert (entry["images"], entry["characters"]) == (12, 1)
    assert json.loads(entry["skipped"]) == {"sheet is not 576x768": 1}

    strips = {row["id"]: row for row in rows(layout, "lpc-action")}
    walk = strips["lpc-action/char_00000/walk/right"]
    slash = strips["lpc-action/char_00000/slash/back"]

    assert (walk["action"], walk["width"], walk["height"]) == ("walk", 576, 64)
    assert (slash["action"], slash["width"]) == ("slash", 384)

    for row in strips.values():
        image = load_image(layout.raw, row)
        assert image.size == (row["width"], 64)
        assert image.getpixel((10, 32)) == QUADRANT_COLORS[row["view"]]


def test_moss_views_come_from_the_prompt_and_captions_keep_the_subject(tmp_path):
    layout = Layout(tmp_path)
    entry = import_source(fake_moss_64(layout), layout)

    assert (entry["images"], entry["characters"]) == (4, 3)
    assert json.loads(entry["skipped"]) == {"image file is missing": 2}

    found = {row["id"]: row for row in rows(layout, "moss-64")}

    assert found["moss-64/characters-cook-v01"]["view"] == "front-left"
    assert found["moss-64/characters-cook-v02"]["view"] == "front-right"
    assert found["moss-64/food-pie-v01"]["view"] is None
    assert found["moss-64/vehicles-cart-v01"]["view"] == "left"
    assert found["moss-64/vehicles-cart-v01"]["source_split"] == "validation"
    assert found["moss-64/characters-cook-v01"]["character"] == "moss-64/characters-cook"
    assert found["moss-64/characters-cook-v01"]["caption"] == "a cook in a white hat"
    assert load_image(layout.raw, found["moss-64/food-pie-v01"]).getpixel((0, 0)) == (100, 80, 40, 255)


def test_parquet_pictures_each_become_one_record_that_loads_back(tmp_path):
    layout = Layout(tmp_path)
    entry = import_source(fake_icons(layout), layout)

    assert (entry["images"], entry["characters"]) == (5, 5)
    assert json.loads(entry["skipped"]) == {"row has no picture": 1}

    found = {row["id"]: row for row in rows(layout, "icons-172k")}
    last = found["icons-172k/train-00000-of-00001/4"]

    # Five rows in groups of two: the fifth is the first row of the third group.
    assert last["member"] == "image#2:0"
    assert (last["width"], last["height"], last["source_split"]) == (32, 32, "train")
    assert last["caption"] == "pixel art icon of thing 4"
    assert load_image(layout.raw, last).getpixel((0, 0)) == (80, 0, 0, 255)


def test_landscapes_keep_each_scene_at_its_three_sizes(tmp_path):
    layout = Layout(tmp_path)
    entry = import_source(fake_landscapes(layout), layout)

    assert (entry["images"], entry["characters"]) == (6, 2)

    found = {row["id"]: row for row in rows(layout, "landscapes-20k")}
    big = found["landscapes-20k/0000001/256"]

    assert big["character"] == "landscapes-20k/0000001"
    assert big["caption"] == "a warm beach"
    assert load_image(layout.raw, big).size == (256, 256)
    assert load_image(layout.raw, big).getpixel((5, 5)) == (0, 0, 2, 255)


def test_records_from_before_the_characters_table_get_one_row_per_character(tmp_path):
    layout = Layout(tmp_path)
    import_source(fake_pac(layout), layout)

    db = connect(layout.records)
    with db:
        db.execute("DELETE FROM characters")
    db.close()

    db = connect(layout.records)
    try:
        names = [row[0] for row in db.execute("SELECT character FROM characters ORDER BY first_rowid")]
    finally:
        db.close()

    assert names == ["pac/test/0", "pac/train/0", "pac/train/1"]
