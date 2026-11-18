import re
from pathlib import Path

import pytest

from pixel_data.sources import Layout, Source, folder_size, is_gathered, load_sources, pick_sources

SOURCES_FILE = Path(__file__).parent.parent / "sources.json"


def test_every_source_is_complete():
    sources = load_sources(SOURCES_FILE)

    ids = [source.id for source in sources]
    assert len(ids) == len(set(ids))

    for source in sources:
        assert source.use in {"train", "eval", "experimental"}
        assert source.license and source.tasks

        if source.kind in {"huggingface", "git"}:
            assert re.fullmatch(r"[0-9a-f]{40}", source.revision), source.id
        else:
            assert source.links, source.id


def test_experimental_sources_live_apart(tmp_path):
    layout = Layout(tmp_path)
    kept = Source("kept", "huggingface", "MIT", "train", ["create"])
    experiment = Source("risky", "manual", "unknown", "experimental", ["create"])

    assert layout.source_dir(kept) == tmp_path / "raw" / "kept"
    assert layout.source_dir(experiment) == tmp_path / "raw" / "_experimental" / "risky"


def test_unknown_source_names_are_refused():
    sources = load_sources(SOURCES_FILE)

    with pytest.raises(SystemExit, match="Unknown source: nope"):
        pick_sources(sources, ["pac", "nope"])


def test_a_manual_source_counts_once_it_has_files(tmp_path):
    layout = Layout(tmp_path)
    source = Source("packs", "manual", "CC0", "train", ["rotate"], links=["https://example.com"])
    folder = layout.source_dir(source)
    folder.mkdir(parents=True)

    (folder / "DROP-FILES-HERE.txt").write_text("links")
    assert not is_gathered(source, layout)

    (folder / "pack.zip").write_bytes(b"zip")
    assert is_gathered(source, layout)


def test_folder_size_skips_download_caches(tmp_path):
    (tmp_path / "a.png").write_bytes(b"1234")
    (tmp_path / ".cache").mkdir()
    (tmp_path / ".cache" / "lock").write_bytes(b"123456789")

    assert folder_size(tmp_path) == (1, 4)
