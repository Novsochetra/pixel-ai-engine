import pytest
from test_animate_page import knight, sprite_png
from test_studio import fake_data

from pixel_data.dashboard.rotate_job import rotate_job
from pixel_data.dashboard.studio import Invalid

LORA = "runs/rotate-v2/final"


@pytest.fixture
def data(tmp_path):
    fake_data(tmp_path)
    knight(tmp_path)
    (tmp_path / "uploads").mkdir()
    (tmp_path / "uploads" / "20261125-100000-slime.png").write_bytes(sprite_png())

    return tmp_path


def test_a_generated_character_becomes_rotate_arguments(data):
    title, args = rotate_job(data, {"source": "generated/knight/s1", "lora": LORA, "turn_model": "flux2-klein-base-4b",
                                    "sprite": "64", "views_list": ["right", "left"]})

    assert title == "Rotate knight s1: 2 views"
    assert args == ["rotate", str((data / "generated" / "knight").resolve()), "--seeds", "1",
                    "--lora", str(data.resolve() / LORA), "--turn-model", "flux2-klein-base-4b", "--sprite", "64",
                    "--views", "left", "right"]


def test_an_upload_is_turned_to_every_view_by_default(data):
    title, args = rotate_job(data, {"source": "uploads/20261125-100000-slime.png", "lora": LORA})

    assert title == "Rotate 20261125-100000-slime: 3 views"
    assert args[1] == str((data / "uploads" / "20261125-100000-slime.png").resolve())
    assert args[2:4] == ["--lora", str(data.resolve() / LORA)]
    assert args[-7:] == ["flux2-klein-4b", "--sprite", "128", "--views", "left", "back", "right"]


def test_a_folder_alone_turns_its_first_character(data):
    _, args = rotate_job(data, {"source": "generated/knight", "lora": "runs/rotate-v2/checkpoints/step-000010"})

    assert args[2:4] == ["--seeds", "0"]


@pytest.mark.parametrize(("form", "message"), [
    ({"source": "generated/knight/s7"}, "knight has no front view for s7"),
    ({"source": "generated/nobody/s0"}, "Pick a character from the list."),
    ({"source": "uploads/../../secret.png"}, "Pick a uploaded picture from the list."),
    ({"source": "generated/knight/s0", "lora": "runs/create-v1/final"}, "Pick a rotate LoRA from the list."),
    ({"source": "generated/knight/s0", "lora": ""}, "Pick a rotate LoRA from the list."),
    ({"source": "generated/knight/s0", "lora": LORA, "sprite": "100"}, "Pick a sprite size"),
    ({"source": "generated/knight/s0", "lora": LORA, "turn_model": "flux3"}, "Pick a turning model"),
    ({"source": "generated/knight/s0", "lora": LORA, "views_list": []}, "Pick at least one view"),
    ({"source": "generated/knight/s0", "lora": LORA, "views_list": ["front"]}, "Pick at least one view"),
])
def test_a_bad_form_is_refused_with_the_reason(data, form, message):
    with pytest.raises(Invalid, match=message):
        rotate_job(data, form)
