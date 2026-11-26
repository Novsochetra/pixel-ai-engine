from pathlib import Path

from pixel_data.dashboard import studio


def run_list(data: Path, job: dict | None) -> dict:
    training = training_run(job)
    loras = studio.lora_options(data)

    return {"runs": [run_entry(run, loras, run["name"] == training) for run in studio.read_runs(data)]}


# The run a job is training now: its args name it, whether it started or resumed it.
def training_run(job: dict | None) -> str | None:
    if not job or job["status"] != "running":
        return None

    args = job.get("args") or []

    if args[:1] != ["train"] or "--name" not in args[:-1]:
        return None

    return args[args.index("--name") + 1]


# Logs written before pixel-train counted the passes over the data have none.
def latest_passes(rows: list[dict]) -> float | None:
    return next((row["passes"] for row in reversed(rows) if "passes" in row), None)


def run_entry(run: dict, loras: list[tuple[str, str]], is_training: bool) -> dict:
    settings = run["settings"]
    rows = run["rows"]
    prefix = f"runs/{run['name']}/"

    return {
        "name": run["name"],
        "task": studio.task_of(run),
        "createdAt": run["created_at"],
        "model": settings.get("model", ""),
        "size": settings.get("size"),
        "export": settings.get("export", ""),
        "sources": settings.get("sources") or [],
        "moreExports": settings.get("more_exports") or [],
        "step": run["step"],
        "steps": run["steps"],
        "secondsPerStep": run["seconds_per_step"],
        "passes": latest_passes(rows),
        "checkpoints": run["checkpoints"],
        "final": run["final"],
        "loss": [[row["step"], row["loss"]] for row in rows if "loss" in row],
        "val": [[step, value] for step, value in run["val"]],
        "tryouts": [{"value": value, "label": label.split(" · ")[-1]} for value, label in loras
                    if value.startswith(prefix)],
        "isTraining": is_training,
    }
