from training_data import SETTINGS, write_run

from pixel_server.training.run_list import run_list


# A resumed run logs the steps after its last checkpoint again; the chart takes the later line once.
def test_a_resumed_run_has_one_loss_per_step(tmp_path):
    rows = [{"step": step, "loss": 0.2} for step in (1, 2, 3)] + [{"step": 3, "loss": 0.5}, {"step": 4, "loss": 0.4}]
    write_run(tmp_path, "rotate-v2", {"created_at": "2026-11-20T10:00:00+00:00", "settings": SETTINGS}, rows)

    run = run_list(tmp_path, None)["runs"][0]

    assert run["loss"] == [[1, 0.2], [2, 0.2], [3, 0.5], [4, 0.4]]


# Runs from before 2026-11-26 were trained without the passes; a resume adds them from then on.
def test_a_run_resumed_after_passes_were_logged_shows_the_latest(tmp_path):
    rows = [{"step": 1, "loss": 0.2}, {"step": 2, "loss": 0.2, "passes": 0.0002}, {"step": 3, "loss": 0.2}]
    write_run(tmp_path, "create-v1", {"created_at": "2026-11-22T18:27:15+00:00", "settings": {"task": "create"}}, rows)

    run = run_list(tmp_path, None)["runs"][0]

    assert run["passes"] == 0.0002
    assert (run["task"], run["size"], run["steps"]) == ("create", None, 0)
