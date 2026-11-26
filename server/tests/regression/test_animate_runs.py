import json

from conftest import save_png
from PIL import Image

from pixel_server.animate.animated_list import animated_list


# The first runs (2026-11-23) kept no subject, no same_end and no count of used frames, and a
# relative source path.
def test_an_early_run_reads_with_its_gaps_filled(tmp_path):
    run = tmp_path / "animated" / "knight-test"
    save_png(run / "s0-right-walk-sheet.png")
    Image.new("RGB", (8, 8)).save(run / "s0-right-walk.gif")
    info = {"created_at": "2026-11-23T03:51:22+00:00", "source": "../dataset/data/generated/knight", "size": 512,
            "frames": 17, "clips": [{"id": "s0-right-walk", "seed": 0, "frames": 17, "kept": 8}]}
    (run / "animated.json").write_text(json.dumps(info))

    entry = animated_list(tmp_path)["runs"][0]

    assert entry["source"] == "knight"
    assert entry["subject"] == ""
    assert entry["openEnd"] is False
    assert entry["clips"][0] | {"gif": None, "raw": None, "sheet": None} == {
        "id": "s0-right-walk", "seed": 0, "view": "right", "action": "walk", "kept": 8, "used": None,
        "gif": None, "raw": None, "sheet": None,
    }


def test_a_clip_whose_gif_is_not_written_yet_is_left_out(tmp_path):
    run = tmp_path / "animated" / "running"
    run.mkdir(parents=True)
    info = {"created_at": "2026-11-25T03:00:00", "clips": [{"id": "s0-front-idle", "kept": 8}]}
    (run / "animated.json").write_text(json.dumps(info))

    assert animated_list(tmp_path)["runs"][0]["clips"] == []
