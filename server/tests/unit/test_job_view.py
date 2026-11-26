from pixel_server.job_view import job_view, last_line, progress_of

RUNNING = {
    "id": "20261124-153908",
    "kind": "animate",
    "title": "Animate a dragon",
    "status": "running",
    "started_at": "2026-11-24T08:39:08+00:00",
    "ended_at": None,
}


def test_last_line_skips_blank_lines():
    assert last_line("turning 1 of 3\n  done in 26s\n\n") == "done in 26s"


def test_last_line_of_empty_log():
    assert last_line("") == ""


def test_progress_reads_the_last_bar():
    log = "Loading: 100%|██████████| 5/5\nturning 2 of 3\n 60%|██████    | 3/5 [00:01<00:00]"

    assert progress_of(log) == 0.6


def test_progress_is_unknown_when_the_last_line_has_no_bar():
    assert progress_of("Loading: 100%|██████████| 5/5\nturning 2 of 3: s0 back...") is None


def test_view_without_a_job():
    assert job_view(None, "") == {"job": None, "progress": None, "step": "", "log": ""}


def test_view_of_a_running_job():
    view = job_view(RUNNING, "turning 1 of 3\n 25%|██  | 1/4")

    assert view["job"]["startedAt"] == RUNNING["started_at"]
    assert view["progress"] == 0.25
    assert view["step"] == "25%|██  | 1/4"


def test_view_of_a_finished_job_has_no_progress():
    view = job_view({**RUNNING, "status": "done"}, " 25%|██  | 1/4")

    assert view["progress"] is None
    assert view["step"] == ""
