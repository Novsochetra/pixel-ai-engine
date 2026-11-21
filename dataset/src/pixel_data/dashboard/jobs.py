"""Runs `pixel-train` commands for the dashboard, one at a time, and remembers them.

The models live in training/, in their own environment, so the dashboard starts them as a separate
process instead of importing them. Only one job runs at a time: each one fills most of a 32 GB Mac.
Every job gets a folder under data/jobs/ with its settings (job.json) and its output (log.txt), so
the dashboard can show it after a reload or a restart.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

TRAINING = Path(__file__).resolve().parents[4] / "training"
LOG_TAIL = 4000
COLOURS = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_command() -> list[str]:
    # caffeinate keeps a Mac awake while a long run works; elsewhere it is not there and not needed.
    awake = ["caffeinate", "-i"] if shutil.which("caffeinate") else []

    return [*awake, "uv", "run", "pixel-train"]


@dataclass
class Jobs:
    folder: Path
    data: Path
    command: list[str] = field(default_factory=default_command)
    cwd: Path = TRAINING
    _process: subprocess.Popen | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        # A job that was running when the dashboard stopped has no process any more.
        for job in self.all():
            if job["status"] == "running":
                self._finish(job["id"], "stopped", None)

    def all(self) -> list[dict]:
        jobs = [json.loads(path.read_text()) for path in self.folder.glob("*/job.json")]

        return sorted(jobs, key=lambda job: job["id"], reverse=True)

    def current(self) -> dict | None:
        jobs = self.all()

        return jobs[0] if jobs and jobs[0]["status"] == "running" else None

    def latest(self) -> dict | None:
        jobs = self.all()

        return jobs[0] if jobs else None

    def log(self, job_id: str, tail: int = LOG_TAIL) -> str:
        path = self.folder / job_id / "log.txt"
        if not path.exists():
            return ""

        # Bytes, not read_text: that would turn each "\r" into a new line.
        text = COLOURS.sub("", path.read_bytes().decode("utf-8", "replace"))
        # Progress bars redraw a line with \r; only the last drawing of each line matters.
        # (split on "\n" only: splitlines would also split on "\r").
        lines = [line.rstrip("\r").rsplit("\r", 1)[-1] for line in text.split("\n")]

        return "\n".join(lines)[-tail:]

    def start(self, kind: str, title: str, args: list[str]) -> dict:
        with self._lock:
            if self.current():
                raise RuntimeError("Another job is running. Wait for it, or stop it first.")

            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            job_id, number = stamp, 1
            while (self.folder / job_id).exists():
                number += 1
                job_id = f"{stamp}-{number}"
            folder = self.folder / job_id
            folder.mkdir(parents=True)
            job = {"id": job_id, "kind": kind, "title": title, "args": args, "status": "running",
                   "started_at": now(), "ended_at": None, "returncode": None}
            self._write(job)

            log = (folder / "log.txt").open("w")
            env = {**os.environ, "HF_HUB_OFFLINE": "1", "PYTHONUNBUFFERED": "1", "NO_COLOR": "1"}
            # The dashboard's own environment is not the one training/ runs in.
            env.pop("VIRTUAL_ENV", None)
            # Its own process group, so Stop reaches uv, Python and caffeinate together.
            self._process = subprocess.Popen(
                [*self.command, "--data", str(self.data.resolve()), *args], cwd=self.cwd, env=env,
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True,
            )
            threading.Thread(target=self._wait, args=(job_id, self._process, log), daemon=True).start()

            return job

    def stop(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            return

        job = self.current()
        if job:
            job["stopping"] = True
            self._write(job)

        # Ctrl+C first, as in a terminal: training then stops between steps.
        os.killpg(process.pid, signal.SIGINT)
        deadline = time.monotonic() + 20
        while process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.2)
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)

    def _wait(self, job_id: str, process: subprocess.Popen, log) -> None:
        code = process.wait()
        log.close()
        job = json.loads((self.folder / job_id / "job.json").read_text())
        status = "stopped" if job.get("stopping") else ("done" if code == 0 else "failed")
        self._finish(job_id, status, code)

    def _finish(self, job_id: str, status: str, code: int | None) -> None:
        path = self.folder / job_id / "job.json"
        job = json.loads(path.read_text())
        job.update(status=status, returncode=code, ended_at=now())
        job.pop("stopping", None)
        self._write(job)

    def _write(self, job: dict) -> None:
        path = self.folder / job["id"] / "job.json"
        partial = path.with_suffix(".partial")
        partial.write_text(json.dumps(job, indent=2))
        partial.replace(path)
