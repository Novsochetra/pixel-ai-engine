import json

from conftest import save_png

from pixel_server.rotate.rotated_list import rotated_list


def write_generated(data, folder: str, views: list[str], info: dict) -> None:
    for view in views:
        save_png(data / "generated" / folder / f"s0-{view}.png")

    (data / "generated" / folder / "generated.json").write_text(json.dumps(info))


# A side view drawn by Generate has a left view too, but it is the right one flipped, not turned.
def test_only_characters_a_rotate_lora_turned_are_listed(tmp_path):
    write_generated(tmp_path, "test-side-flying", ["right", "left"],
                    {"prompt": "a dragon", "facing": "side", "created_at": "2026-11-24T08:30:08+00:00"})
    write_generated(tmp_path, "front-only", ["front"], {"prompt": "a frog", "lora": "/d/runs/rotate-v2/final"})
    write_generated(tmp_path, "knight", ["front", "left", "back", "right"],
                    {"prompt": "a knight", "created_at": "2026-11-21T04:40:45+00:00",
                     "lora": "../dataset/data/runs/rotate-v2/final", "turn_model": "flux2-klein-4b", "size": 256})

    characters = rotated_list(tmp_path)["characters"]

    assert [character["key"] for character in characters] == ["knight/s0"]
    assert (characters[0]["sprite"], characters[0]["turnWith"]) == (64, "rotate-v2 · final")
