import asyncio

import pytest
from pixel_data.dashboard import animate
from pixel_data.dashboard.studio import Invalid

from pixel_server.animate.animate_form import old_form
from pixel_server.animate.animate_options import animate_options, made_source
from pixel_server.animate.animated_list import clip_entry
from pixel_server.animate.upload import TooBig, read_capped, save_png


async def chunks(*parts: bytes):
    for part in parts:
        yield part


def test_the_views_become_the_old_checkbox_list():
    body = {"source": "generated/knight/s0", "views": ["front"], "actions": "walk", "steps": 9}

    assert old_form(body) == {"source": "generated/knight/s0", "views_list": ["front"], "actions": "walk"}


@pytest.mark.parametrize("body", [{"size": 384}, {"subject": None}, {"views": ["front", 2]}, {"views": "front"}])
def test_a_field_of_the_wrong_kind_is_invalid(body):
    with pytest.raises(Invalid):
        old_form(body)


def test_a_clip_of_a_generated_character_has_its_view_and_action():
    entry = clip_entry("run", {"id": "s1-left-flaps-its-wings", "kept": 8, "used": 30})

    assert (entry["seed"], entry["view"], entry["action"], entry["kept"]) == (1, "left", "flaps-its-wings", 8)
    assert entry["sheet"] == "/api/files/animated/run/s1-left-flaps-its-wings-sheet.png"
    assert entry["raw"] == "/api/files/animated/run/s1-left-flaps-its-wings-raw.gif"


def test_a_clip_of_an_uploaded_picture_has_no_view():
    entry = clip_entry("run", {"id": "s0-hops", "kept": 8})

    assert (entry["view"], entry["action"]) == (None, "hops")


def test_a_character_lists_a_picture_for_each_view():
    item = {"folder": "knight", "prompt": "a knight"}

    source = made_source(item, 2, ["front", "back"])

    assert source["value"] == "generated/knight/s2"
    assert source["pictures"] == {"front": "/api/files/generated/knight/s2-front.png",
                                  "back": "/api/files/generated/knight/s2-back.png"}


def test_the_options_come_from_the_old_form():
    options = animate_options()

    assert [size["value"] for size in options["sizes"]] == list(animate.SIZES)
    assert [frames["value"] for frames in options["frames"]] == list(animate.FRAMES)
    assert {"size": "512", "frames": "17", "minutes": 8} in options["minutes"]
    assert options["defaults"]["actions"] == animate.DEFAULT_ACTIONS


def test_a_body_under_the_limit_is_read_whole():
    assert asyncio.run(read_capped(chunks(b"ab", b"cd"), 4)) == b"abcd"


def test_a_body_over_the_limit_is_cut_off():
    with pytest.raises(TooBig):
        asyncio.run(read_capped(chunks(b"ab", b"cd", b"e"), 4))


def test_only_a_png_is_saved(tmp_path):
    with pytest.raises(Invalid, match="not a PNG"):
        save_png(tmp_path, "a.jpg", b"\xff\xd8\xff\xe0 a jpeg")

    assert not (tmp_path / "uploads").exists()
