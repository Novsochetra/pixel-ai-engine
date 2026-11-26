import pytest
from pixel_data.dashboard.studio import Invalid

from pixel_server.rotate.rotate_form import rotate_form
from pixel_server.rotate.rotated_list import character_entry


def test_the_api_names_become_the_old_form_names():
    body = {"source": "generated/frog/s0", "lora": "runs/r/final", "turningModel": "m", "sprite": "64",
            "views": ["back"], "seeds": 3}

    assert rotate_form(body) == {"source": "generated/frog/s0", "lora": "runs/r/final", "turn_model": "m",
                                 "sprite": "64", "views_list": ["back"]}


@pytest.mark.parametrize("body", [{"lora": None}, {"turningModel": 4}, {"views": ["back", 1]}])
def test_a_field_of_the_wrong_kind_is_invalid(body):
    with pytest.raises(Invalid):
        rotate_form(body)


def test_a_character_made_by_generate_names_no_source():
    entry = character_entry({"folder": "knight", "lora": "../runs/rotate-v2/final"}, 1, ["front", "right"])

    assert (entry["key"], entry["prompt"], entry["rotatedFrom"], entry["sprite"]) == ("knight/s1", "knight", "", 64)
    assert entry["views"][1] == {"label": "Right", "src": "/api/files/generated/knight/s1-right.png"}
