import json

import pytest
from helpers import QUADRANT_COLORS, fake_lpc_4view, fake_pac

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

    with pytest.raises(SystemExit, match="Importers so far: lpc-4view, pac"):
        import_source(source, layout)


def test_a_source_must_be_downloaded_before_import(tmp_path):
    layout = Layout(tmp_path)
    source = Source("pac", "huggingface", "CC-BY-NC-4.0", "train", ["rotate"])

    with pytest.raises(SystemExit, match="Run `pixel gather pac` first"):
        import_source(source, layout)
