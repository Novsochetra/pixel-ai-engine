import pytest
from pixel_data.dashboard import studio

from pixel_server.training.run_list import latest_passes, run_entry, training_run
from pixel_server.training.training_form import resume_form, start_form, tryout_form
from pixel_server.training.training_options import source_entry, training_options

RUNNING = {"status": "running", "args": ["train", "--name", "pixie-draw-v1", "--resume", "--steps", "500"]}


def test_the_sources_become_the_old_checkbox_list():
    body = {"name": "rotate-v3", "steps": 400, "sources": ["pac"], "extra": 1}

    assert start_form(body) == {"name": "rotate-v3", "steps": "400", "sources_list": ["pac"]}


def test_a_new_run_with_no_sources_sends_an_empty_list():
    assert start_form({"name": "a"})["sources_list"] == []


def test_the_tryout_fields_get_their_old_names():
    body = {"run": "r", "checkpoint": "runs/r/final", "model": "m", "characters": 3}

    assert tryout_form(body) == {"run": "r", "lora": "runs/r/final", "model": "m", "rotate": "3"}


@pytest.mark.parametrize("body", [{"sources": ["pac", 2]}, {"sources": "pac"}, {"name": None}, {"steps": True}])
def test_a_field_of_the_wrong_kind_is_invalid(body):
    with pytest.raises(studio.Invalid):
        start_form(body)


def test_a_resume_keeps_only_its_two_fields():
    assert resume_form({"run": "r", "steps": 900, "task": "create"}) == {"run": "r", "steps": "900"}


def test_a_running_train_job_names_its_run():
    assert training_run(RUNNING) == "pixie-draw-v1"


@pytest.mark.parametrize("job", [
    None,
    {**RUNNING, "status": "done"},
    {"status": "running", "args": ["tryout", "--name", "pixie-draw-v1-step"]},
    {"status": "running", "args": ["train", "--name"]},
    {"status": "running"},
])
def test_no_run_is_trained_by_another_job(job):
    assert training_run(job) is None


def test_the_latest_passes_skip_rows_without_them():
    assert latest_passes([{"step": 1, "passes": 0.01}, {"step": 2, "passes": 0.02}, {"step": 3}]) == 0.02
    assert latest_passes([{"step": 1}]) is None


def test_a_run_entry_lists_only_its_own_checkpoints():
    run = {"name": "a", "settings": {}, "created_at": "", "rows": [{"step": 1, "loss": 0.3}], "step": 1, "steps": 9,
           "seconds_per_step": None, "val": [], "checkpoints": [], "final": False}
    loras = [("runs/a/final", "a · final"), ("runs/ab/final", "ab · final")]

    entry = run_entry(run, loras, False)

    assert entry["tryouts"] == [{"value": "runs/a/final", "label": "final"}]
    assert (entry["task"], entry["sources"], entry["loss"]) == ("rotate", [], [[1, 0.3]])


def test_a_source_without_details_has_no_licence():
    assert source_entry("odd", "CC0") == {"name": "odd", "licence": "", "use": ""}


def test_the_options_come_from_the_old_form(tmp_path):
    options = training_options(tmp_path)

    assert [model["value"] for model in options["models"]] == list(studio.MODELS)
    assert [size["value"] for size in options["sizes"]] == [str(size) for size in studio.SIZES]
    assert options["namePattern"] == studio.NAME.pattern
    assert options["exports"] == []
