import json
import sys
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest
from helpers import fake_pac

from pixel_data.dashboard import studio
from pixel_data.dashboard.browse_server import serve
from pixel_data.dashboard.jobs import Jobs
from pixel_data.gather.importer import import_source
from pixel_data.sources import Layout

FAKE_TRAIN = """
import sys, time
print("args", " ".join(sys.argv[1:]), flush=True)
print("step 1/2: loss 0.2\\rstep 2/2: loss 0.1", flush=True)
if "sleep" in sys.argv:
    time.sleep(30)
sys.exit(3 if "fail" in sys.argv else 0)
"""


def fake_data(data: Path) -> Path:
    run = data / "runs" / "rotate-v2"
    (run / "checkpoints" / "step-000010").mkdir(parents=True)
    (run / "checkpoints" / "step-000010" / "state.json").write_text('{"step": 10}')
    (run / "final").mkdir()
    (run / "final" / "pytorch_lora_weights.safetensors").write_text("lora")
    settings = {"model": "flux2-klein-base-4b", "export": "rotation-v1", "size": 256, "steps": 20, "rank": 16,
                "learning_rate": 0.0001, "accumulate": 4, "every": 10, "val_count": 16, "sources": ["pac"], "seed": 0}
    (run / "run.json").write_text(json.dumps({"created_at": "2026-11-20T10:00:00+00:00", "settings": settings}))
    rows = [{"step": step, "loss": 0.2 - step / 200, "seconds_per_step": 27.0} for step in range(1, 21)]
    rows[9]["val_loss"], rows[19]["val_loss"] = 0.15, 0.12
    # A resumed run logs steps 11-12 twice; the later lines count.
    rows += [{"step": 11, "loss": 0.5, "seconds_per_step": 27.0}]
    (run / "log.jsonl").write_text("\n".join(json.dumps(row) for row in rows))

    export = data / "exports" / "rotation-v1"
    export.mkdir(parents=True)
    (export / "characters.jsonl").write_text("")
    (export / "export.json").write_text(json.dumps({"sources": {"pac": {"license": "CC-BY-NC-4.0"},
                                                                "lpc-4view": {"license": "CC-BY-SA-3.0"}}}))

    create = data / "runs" / "create-v1"
    (create / "final").mkdir(parents=True)
    (create / "final" / "pytorch_lora_weights.safetensors").write_text("lora")
    (create / "run.json").write_text(json.dumps({"created_at": "2026-11-23T10:00:00+00:00",
                                                 "settings": {**settings, "task": "create"}}))

    generated = data / "generated" / "frog"
    generated.mkdir(parents=True)
    (generated / "generated.json").write_text(json.dumps({"created_at": "2026-11-21T04:50:09+00:00", "prompt": "a frog wizard",
                                                          "lora": "runs/rotate-v2/final", "turn_model": "flux2-klein-4b", "sprite": 128}))
    (generated / "s0-sheet.png").write_bytes(b"png")

    return data


def fake_jobs(tmp_path: Path) -> Jobs:
    script = tmp_path / "fake_train.py"
    script.write_text(FAKE_TRAIN)

    return Jobs(tmp_path / "data" / "jobs", tmp_path / "data", command=[sys.executable, str(script)], cwd=tmp_path)


def wait_until_done(jobs: Jobs, seconds: float = 10) -> dict:
    deadline = time.monotonic() + seconds
    while jobs.current() and time.monotonic() < deadline:
        time.sleep(0.05)

    return jobs.latest()


def test_a_job_runs_pixel_train_with_the_data_folder_and_keeps_its_log(tmp_path):
    jobs = fake_jobs(tmp_path)

    jobs.start("generate", "Generate: a frog", ["generate", "a frog"])
    job = wait_until_done(jobs)

    assert job["status"] == "done" and job["returncode"] == 0
    log = jobs.log(job["id"])
    assert f"args --data {(tmp_path / 'data').resolve()} generate a frog" in log
    assert "step 2/2: loss 0.1" in log and "step 1/2" not in log


def test_a_failed_job_is_marked_failed(tmp_path):
    jobs = fake_jobs(tmp_path)

    jobs.start("train", "Train", ["train", "fail"])

    assert wait_until_done(jobs)["status"] == "failed"


def test_only_one_job_runs_at_a_time_and_stop_ends_it(tmp_path):
    jobs = fake_jobs(tmp_path)
    jobs.start("train", "Train", ["train", "sleep"])

    with pytest.raises(RuntimeError):
        jobs.start("generate", "Generate", ["generate", "x"])

    jobs.stop()
    assert wait_until_done(jobs)["status"] == "stopped"


def test_a_job_left_running_by_a_closed_dashboard_is_marked_stopped(tmp_path):
    folder = tmp_path / "data" / "jobs" / "20261121-100000"
    folder.mkdir(parents=True)
    (folder / "job.json").write_text(json.dumps({"id": "20261121-100000", "status": "running", "title": "Train"}))

    assert fake_jobs(tmp_path).latest()["status"] == "stopped"


def test_runs_are_read_with_the_later_log_line_winning(tmp_path):
    run = next(run for run in studio.read_runs(fake_data(tmp_path)) if run["name"] == "rotate-v2")

    assert (run["name"], run["step"], run["steps"]) == ("rotate-v2", 20, 20)
    assert run["val"] == [(10, 0.15), (20, 0.12)]
    assert next(row for row in run["rows"] if row["step"] == 11)["loss"] == 0.5
    assert "<svg" in studio.chart(run)


def test_generate_form_becomes_arguments(tmp_path):
    data = fake_data(tmp_path)

    title, args = studio.generate_job(data, {"prompt": "  a frog   wizard ", "seeds": "3", "sprite": "128",
                                             "turn_model": "flux2-klein-4b", "lora": "runs/rotate-v2/final"})

    assert title == "Generate: a frog wizard"
    assert args == ["generate", "a frog wizard", "--seeds", "3", "--sprite", "128", "--turn-model", "flux2-klein-4b",
                    "--front-model", "flux2-klein-4b", "--lora", str(data.resolve() / "runs/rotate-v2/final")]


def test_a_create_lora_draws_and_a_rotate_lora_turns(tmp_path):
    data = fake_data(tmp_path)

    _, args = studio.generate_job(data, {"prompt": "a frog", "create_lora": "runs/create-v1/final",
                                         "lora": "runs/rotate-v2/final"})

    assert args[args.index("--create-lora") + 1] == str(data.resolve() / "runs/create-v1/final")
    with pytest.raises(studio.Invalid):
        studio.generate_job(data, {"prompt": "a frog", "lora": "runs/create-v1/final"})
    with pytest.raises(studio.Invalid):
        studio.generate_job(data, {"prompt": "a frog", "create_lora": "runs/rotate-v2/final"})
    with pytest.raises(studio.Invalid):
        studio.tryout_job(data, {"run": "create-v1", "lora": "runs/create-v1/final", "model": "flux2-klein-4b"})
    _, resume = studio.resume_job(data, {"run": "create-v1", "steps": "40"})
    assert resume[4:6] == ["--task", "create"]


def test_a_pose_goes_to_the_prompt_and_empty_means_standing(tmp_path):
    data = fake_data(tmp_path)

    _, args = studio.generate_job(data, {"prompt": "a dragon", "pose": "  flying,  wings spread "})
    _, plain = studio.generate_job(data, {"prompt": "a dragon", "pose": ""})

    assert args[args.index("--pose") + 1] == "flying, wings spread"
    assert "--pose" not in plain
    with pytest.raises(studio.Invalid):
        studio.generate_job(data, {"prompt": "a dragon", "pose": "flying", "create_lora": "runs/create-v1/final"})


def test_a_side_view_is_drawn_without_turning(tmp_path):
    data = fake_data(tmp_path)

    _, args = studio.generate_job(data, {"prompt": "a dragon", "facing": "side", "lora": "runs/rotate-v2/final"})

    assert args[-2:] == ["--facing", "side"]
    assert "--lora" not in args
    with pytest.raises(studio.Invalid):
        studio.generate_job(data, {"prompt": "a dragon", "facing": "side", "create_lora": "runs/create-v1/final"})


@pytest.mark.parametrize("form", [
    {"prompt": ""},
    {"prompt": "x", "facing": "up"},
    {"prompt": "x", "pose": "x" * 101},
    {"prompt": "x", "seeds": "99"},
    {"prompt": "x", "sprite": "65"},
    {"prompt": "x", "lora": "../../etc"},
])
def test_generate_form_refuses_bad_values(tmp_path, form):
    with pytest.raises(studio.Invalid):
        studio.generate_job(fake_data(tmp_path), form)


def test_a_new_run_names_its_sources_only_when_some_are_left_out(tmp_path):
    data = fake_data(tmp_path)
    form = {"name": "rotate-v3", "export": "rotation-v1", "model": "flux2-klein-base-4b", "size": "256", "steps": "2000"}

    _, every = studio.train_job(data, {**form, "sources_list": ["pac", "lpc-4view"]})
    _, some = studio.train_job(data, {**form, "sources_list": ["lpc-4view"]})

    assert "--sources" not in every and every[3:5] == ["--task", "rotate"]
    assert some[-2:] == ["--sources", "lpc-4view"]
    _, create = studio.train_job(data, {**form, "task": "create", "sources_list": ["lpc-4view"]})
    assert create[3:5] == ["--task", "create"]
    with pytest.raises(studio.Invalid):
        studio.train_job(data, {**form, "name": "rotate-v2", "sources_list": ["pac"]})
    with pytest.raises(studio.Invalid):
        studio.train_job(data, {**form, "name": "bad name!", "sources_list": ["pac"]})


def test_resume_keeps_the_settings_of_the_run(tmp_path):
    _, args = studio.resume_job(fake_data(tmp_path), {"run": "rotate-v2", "steps": "40"})

    assert args[:7] == ["train", "--name", "rotate-v2", "--resume", "--task", "rotate", "--steps"]
    assert ["--size", "256"] == args[args.index("--size"):args.index("--size") + 2]
    assert args[-2:] == ["--sources", "pac"]
    with pytest.raises(studio.Invalid):
        studio.resume_job(fake_data(tmp_path / "again"), {"run": "rotate-v2", "steps": "20"})


def test_a_tryout_loads_a_checkpoint_of_that_run_only(tmp_path):
    data = fake_data(tmp_path)

    _, args = studio.tryout_job(data, {"run": "rotate-v2", "lora": "runs/rotate-v2/checkpoints/step-000010",
                                       "model": "flux2-klein-4b", "rotate": "4"})

    assert "--no-create" in args and args[-1] == "rotate-v2-step-000010-fast"
    with pytest.raises(studio.Invalid):
        studio.tryout_job(data, {"run": "rotate-v2", "lora": "runs/other/final", "model": "flux2-klein-4b"})


@pytest.fixture
def site(tmp_path):
    layout = Layout(tmp_path / "data")
    import_source(fake_pac(layout), layout)
    fake_data(layout.data)
    jobs = fake_jobs(tmp_path)

    server = serve(layout, 0, jobs)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}", jobs

    server.shutdown()
    server.server_close()


def post(url: str, form: dict, origin: str | None = None) -> int:
    request = Request(url, data=urlencode(form, doseq=True).encode(), method="POST")
    if origin:
        request.add_header("Origin", origin)
    try:
        with urlopen(request) as response:
            return response.status
    except HTTPError as error:
        return error.code


def test_the_pages_show_runs_and_what_was_made(site):
    url, _ = site

    with urlopen(f"{url}/training") as response:
        training = response.read().decode()
    with urlopen(f"{url}/generate") as response:
        generate = response.read().decode()

    assert "rotate-v2" in training and "step 20 of 20" in training and "<svg" in training
    assert "a frog wizard" in generate and "/generated/frog/s0-sheet.png" in generate


def test_a_form_starts_a_job_and_goes_back_to_the_page(site):
    url, jobs = site

    status = post(f"{url}/generate", {"prompt": "a frog", "seeds": "1", "sprite": "64", "turn_model": "flux2-klein-4b"}, url)

    assert status == 200  # the 303 is followed to the page
    assert wait_until_done(jobs)["title"] == "Generate: a frog"
    with urlopen(f"{url}/jobs/current") as response:
        assert "generate a frog" in json.loads(response.read())["log"]


def test_a_bad_form_is_shown_back_with_the_reason(site):
    url, jobs = site

    assert post(f"{url}/generate", {"prompt": ""}, url) == 400
    assert jobs.latest() is None


def test_another_site_cannot_start_a_job(site):
    url, jobs = site

    assert post(f"{url}/generate", {"prompt": "a frog"}, "https://evil.example") == 403
    assert jobs.latest() is None
