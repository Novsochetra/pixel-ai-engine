import pytest
from pixel_data.dashboard import studio

from pixel_server.create.form_options import form_options
from pixel_server.create.generate_form import studio_form
from pixel_server.create.generated_list import generated_entry, lora_label


def test_a_final_lora_reads_as_its_run():
    assert lora_label("../dataset/data/runs/rotate-v2/final") == "rotate-v2 · final"


def test_a_checkpoint_reads_as_its_run_and_step():
    assert lora_label("/data/runs/create-v1/checkpoints/step-000900") == "create-v1 · step-000900"


def test_no_lora_reads_as_nothing():
    assert lora_label(None) == ""
    assert lora_label("") == ""


def test_a_lora_outside_runs_keeps_its_name():
    assert lora_label("/somewhere/my-lora") == "my-lora"


def test_a_generated_entry_links_each_sheet():
    item = {"folder": "knight", "prompt": "a knight", "created_at": "2026-11-21T04:50:09+00:00",
            "sprite": 128, "front_model": "flux2-klein-4b", "lora": "runs/rotate-v2/final",
            "turn_model": "flux2-klein-4b", "sheets": ["s0-sheet.png", "s1-sheet.png"]}

    entry = generated_entry(item)

    assert entry["sheets"] == [
        {"label": "Character 1", "src": "/api/files/generated/knight/s0-sheet.png"},
        {"label": "Character 2", "src": "/api/files/generated/knight/s1-sheet.png"},
    ]
    assert entry["turnWith"] == "rotate-v2 · final"
    assert entry["turningModel"] == "flux2-klein-4b"
    assert entry["drawWith"] == ""


def test_a_side_view_has_no_turning_model():
    item = {"folder": "dragon", "facing": "side", "turn_model": "flux2-klein-4b", "sheets": ["s0-sheet.png"]}

    entry = generated_entry(item)

    assert entry["facing"] == "side"
    assert entry["turningModel"] == ""
    assert entry["prompt"] == "dragon"


def test_the_form_fields_get_the_old_form_names():
    body = {"prompt": "a frog", "characters": 3, "drawWith": "", "turningModel": "flux2-klein-4b"}

    assert studio_form(body) == {"prompt": "a frog", "seeds": "3", "create_lora": "", "turn_model": "flux2-klein-4b"}


def test_unknown_fields_are_left_out():
    assert studio_form({"prompt": "a frog", "steps": 9}) == {"prompt": "a frog"}


@pytest.mark.parametrize("value", [True, None, ["a frog"], 1.5])
def test_a_field_that_is_not_text_or_a_number_is_invalid(value):
    with pytest.raises(studio.Invalid):
        studio_form({"characters": value})


def test_the_options_come_from_the_old_form():
    options = form_options()

    assert [model["value"] for model in options["models"]] == list(studio.MODELS)
    assert [sprite["value"] for sprite in options["sprites"]] == [str(size) for size in studio.SPRITES]
    assert [facing["value"] for facing in options["facing"]] == ["front", "side"]


def test_a_generated_entry_names_its_reference():
    item = {"folder": "hero", "reference": "/data/uploads/20261127-hero.png", "sheets": ["s0-sheet.png"]}

    assert generated_entry(item)["reference"] == "20261127-hero.png"
    assert generated_entry({"folder": "frog", "sheets": []})["reference"] == ""
