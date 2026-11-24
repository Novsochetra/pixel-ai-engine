import json
from pathlib import Path

import pytest

from pixel_training.cli import needs_login, parser, trained_lora


def test_a_gated_model_without_login_gets_the_login_hint():
    assert needs_login("OSError: Failed to load config from 'black-forest-labs/flux-3-image-klein'.")
    assert needs_login("401 Client Error")
    assert not needs_login("RuntimeError: MPS backend out of memory")


def test_tryout_runs_both_models_by_default():
    args = parser().parse_args(["tryout"])

    assert args.models == ["flux2-klein-4b", "flux2-klein-base-4b", "flux3-klein"]
    assert (args.seeds, args.rotate, args.export) == (2, 4, "rotation-v1")


def make_run(folder, task):
    (folder / "final").mkdir(parents=True)
    (folder / "run.json").write_text(json.dumps({"settings": {"task": task, "size": 256}}))


def test_a_lora_can_be_given_by_its_run_name(tmp_path):
    make_run(tmp_path / "runs" / "create-v1", "create")

    lora, settings = trained_lora(Path("create-v1"), "create", "--create-lora", tmp_path)

    assert lora == tmp_path / "runs" / "create-v1" / "final"
    assert settings["size"] == 256


def test_a_missing_lora_says_not_found_not_the_wrong_task(tmp_path):
    with pytest.raises(SystemExit, match="not found"):
        trained_lora(tmp_path / "nothing", "create", "--create-lora", tmp_path)


def test_a_lora_of_the_other_task_is_refused(tmp_path):
    make_run(tmp_path / "runs" / "rotate-v2", "rotate")

    with pytest.raises(SystemExit, match="is a rotate one"):
        trained_lora(tmp_path / "runs" / "rotate-v2", "create", "--create-lora", tmp_path)
