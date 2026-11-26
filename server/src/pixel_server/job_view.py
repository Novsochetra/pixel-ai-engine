import re

PERCENT = re.compile(r"(\d{1,3})%\|")


def last_line(log: str) -> str:
    lines = [line.strip() for line in log.splitlines() if line.strip()]

    return lines[-1] if lines else ""


def progress_of(log: str) -> float | None:
    found = PERCENT.findall(last_line(log))
    if not found:
        return None

    return min(int(found[-1]), 100) / 100


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
