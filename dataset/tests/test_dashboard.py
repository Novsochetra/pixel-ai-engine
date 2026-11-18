import json
import zipfile

from helpers import png_bytes

from pixel_data.dashboard.build import build_dashboard
from pixel_data.dashboard.page import human_size
from pixel_data.gather.download import matches
from pixel_data.sources import Layout, Source


def gathered_source(layout: Layout) -> Source:
    source = Source("lpc-test", "huggingface", "CC-BY-SA-3.0", "train", ["rotate"], repo="someone/lpc")
    folder = layout.source_dir(source)
    folder.mkdir(parents=True)

    with zipfile.ZipFile(folder / "train.zip", "w") as archive:
        for index in range(3):
            archive.writestr(f"{index}.png", png_bytes())
    (folder / "_source.json").write_text(json.dumps({"gathered_at": "2026-11-18T09:00:00+00:00"}))

    return source


def test_dashboard_shows_previews_and_what_is_missing(tmp_path):
    layout = Layout(tmp_path)
    gathered = gathered_source(layout)
    missing = Source("big-<set>", "huggingface", "MIT", "experimental", ["create"], repo="someone/big")

    page = build_dashboard([gathered, missing], layout)
    html = page.read_text()

    assert (layout.reports / "thumbs" / "lpc-test" / "000.png").exists()
    assert html.count('class="thumb"') == 3
    assert "Run <code>pixel gather big-&lt;set&gt;</code>" in html
    assert "1 of 2" in html


def test_sizes_read_like_a_person_would_write_them():
    assert human_size(512) == "512 B"
    assert human_size(306_400_000) == "306.4 MB"
    assert human_size(53_000_000_000) == "53.0 GB"


def test_allow_patterns_pick_only_the_files_wanted():
    assert matches("2D_Art_03.zip", ["2D_Art*"])
    assert not matches("Music_00.zip", ["2D_Art*", "README.md"])
    assert matches("anything.parquet", [])
