import re

PERCENT = re.compile(r"(\d{1,3})%\|")
# pixel-train writes no bar, only a line a step: "step 125/500: loss ...".
TRAINING_STEP = re.compile(r"^step (\d+)/(\d+):")


def last_line(log: str) -> str:
    lines = [line.strip() for line in log.splitlines() if line.strip()]

    return lines[-1] if lines else ""


def step_share(line: str) -> float | None:
    found = TRAINING_STEP.match(line)
    if not found or int(found[2]) == 0:
        return None

    return min(int(found[1]) / int(found[2]), 1.0)


def progress_of(log: str) -> float | None:
    line = last_line(log)

    found = PERCENT.findall(line)
    if found:
        return min(int(found[-1]), 100) / 100

    return step_share(line)


def job_view(job: dict | None, log: str) -> dict:
    if job is None:
        return {"job": None, "progress": None, "step": "", "log": ""}

    running = job["status"] == "running"

    return {
        "job": {
            "id": job["id"],
            "kind": job["kind"],
            "title": job["title"],
            "status": job["status"],
            "stopping": bool(job.get("stopping")),
            "startedAt": job["started_at"],
            "endedAt": job["ended_at"],
        },
        "progress": progress_of(log) if running else None,
        "step": last_line(log) if running else "",
        "log": log,
    }
