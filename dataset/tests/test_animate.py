import io
import json

import pytest
from PIL import Image

from pixel_data.dashboard import animate
from pixel_data.dashboard.studio import Invalid


def sprite_png(size=(64, 64)) -> bytes:
    picture = Image.new("RGBA", size, (0, 0, 0, 0))
    picture.paste((30, 30, 200, 255), (20, 10, 44, 60))
    buffer = io.BytesIO()
    picture.save(buffer, "PNG")

    return buffer.getvalue()


def knight(data):
    folder = data / "generated" / "knight"
    folder.mkdir(parents=True)
    (folder / "generated.json").write_text(json.dumps({"prompt": "a knight with a sword", "created_at": "2026-11-22T10:00:00+00:00"}))
    for name in ("s0-front", "s0-right", "s0-front-raw", "s1-front"):
        (folder / f"{name}.png").write_bytes(sprite_png())

    return folder


def test_a_generated_character_becomes_animate_arguments(tmp_path):
    data = tmp_path
    folder = knight(data)

    title, args = animate.animate_job(data, {
        "source": "generated/knight/s0", "views_list": ["front", "right"], "actions": "idle\r\n flaps its  wings \n\nIDLE",
        "size": "384", "frames": "33", "subject": "a knight,  empty hands"})

    assert title == "Animate knight: 4 clips"
    assert args[:6] == ["animate", str(folder.resolve()), "--views", "front", "right", "--seeds"]
    assert args[args.index("--actions") + 1:args.index("--size")] == ["idle", "flaps its wings"]
    assert args[args.index("--subject") + 1] == "a knight, empty hands" and "--open-end" not in args
    assert args[args.index("--name") + 1].endswith("-knight")


def test_a_character_offers_only_the_views_it_has(tmp_path):
    knight(tmp_path)

    assert animate.characters(tmp_path)[0]["sprites"] == {0: ["front", "right"], 1: ["front"]}
    with pytest.raises(Invalid, match="s1 has: front"):
        animate.animate_job(tmp_path, {"source": "generated/knight/s1", "views_list": ["right"], "actions": "walk"})
    with pytest.raises(Invalid, match="no character s7"):
        animate.animate_job(tmp_path, {"source": "generated/knight/s7", "views_list": ["front"], "actions": "walk"})


def test_a_link_to_the_folder_picks_its_first_character(tmp_path):
    knight(tmp_path)

    _, args = animate.animate_job(tmp_path, {"source": "generated/knight", "views_list": ["front"], "actions": "walk"})

    assert args[args.index("--seeds") + 1] == "0"


def test_an_upload_is_saved_as_a_clean_png_and_needs_a_subject(tmp_path):
    form = {"source": "upload", "actions": "walk", "files": {"image": ("My Hero!.png", sprite_png((48, 64)))}}

    with pytest.raises(Invalid, match="what the picture shows"):
        animate.animate_job(tmp_path, form)
    title, args = animate.animate_job(tmp_path, {**form, "subject": "a hero in red"})

    saved = list((tmp_path / "uploads").glob("*.png"))
    assert len(saved) == 1 and saved[0].name.endswith("-my-hero.png")
    assert Image.open(saved[0]).size == (48, 64)
    assert args[:4] == ["animate", str(saved[0].resolve()), "--seeds", "0"] and "--views" not in args and "--open-end" not in args
    assert animate.uploads(tmp_path) == [saved[0].name]

    # The same picture can be picked again without uploading it.
    _, again = animate.animate_job(tmp_path, {"source": f"uploads/{saved[0].name}", "subject": "a hero", "actions": "idle"})
    assert again[1] == str(saved[0].resolve())


@pytest.mark.parametrize("body", [b"not a picture", sprite_png((3000, 10))])
def test_a_bad_upload_is_refused(tmp_path, body):
    with pytest.raises(Invalid):
        animate.animate_job(tmp_path, {"source": "upload", "subject": "x", "actions": "walk",
                                            "files": {"image": ("x.png", body)}})
    assert not list((tmp_path / "uploads").glob("*.png")) if (tmp_path / "uploads").exists() else True


def test_only_known_uploads_and_some_actions_are_passed_on(tmp_path):
    with pytest.raises(Invalid):
        animate.animate_job(tmp_path, {"source": "uploads/../../etc.png", "subject": "x", "actions": "walk"})
    with pytest.raises(Invalid, match="at least one action"):
        animate.animate_job(tmp_path, {"source": "upload", "subject": "x", "actions": " \n "})
    with pytest.raises(Invalid, match="at most 8"):
        animate.animate_job(tmp_path, {"source": "upload", "subject": "x", "actions": "\n".join(f"move {n}" for n in range(9))})
