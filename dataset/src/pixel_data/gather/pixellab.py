"""Make characters with the PixelLab API, from the descriptions in pixellab/plan.json.

Each character is a paid call, so this runs only for the number of characters asked for, and a
character already made (or already paid for and still being made) is never asked for again.
"""

import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from pixel_data.sources import Layout, Source

API = "https://api.pixellab.ai/v2"
TOKEN_NAME = "PIXELLAB_SECRET"
# Pictures come back as links; only PixelLab's own hosts are fetched.
PICTURE_DOMAIN = "pixellab.ai"
CHARACTER_FILE = "character.json"
JOB_FILE = "job.json"
FAILED_FILE = "failed.jsonl"
POLL_SECONDS = 6
WAIT_LIMIT = 15 * 60
BUSY_WAIT = 30


class Stop(Exception):
    """A reason to stop every call, such as a bad token or no credits left."""


class Refused(Exception):
    """PixelLab said no to this one character; the others can go on."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_token(env_file: Path) -> str:
    token = os.environ.get(TOKEN_NAME, "").strip()

    if not token and env_file.is_file():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == TOKEN_NAME:
                token = value.strip().strip("'\"")

    if not token:
        raise SystemExit(
            f"No PixelLab token. Copy it from https://pixellab.ai/account and put this line in {env_file}:\n"
            f"  {TOKEN_NAME}=your-token"
        )

    return token


class Api:
    def __init__(self, token: str, base: str = API):
        self.token = token
        self.base = base

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(f"{self.base}{path}", data=data, method=method)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Content-Type", "application/json")

        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    return json.loads(response.read() or b"{}")
            except urllib.error.HTTPError as error:
                detail = error.read().decode(errors="replace")[:500]

                if error.code == 401:
                    raise Stop("PixelLab says the token is wrong (401).") from error
                if error.code == 402:
                    raise Stop("PixelLab says there are no credits left (402).") from error
                if error.code in (429, 529) or error.code >= 500:
                    time.sleep(BUSY_WAIT * (attempt + 1))
                    continue

                raise Refused(f"{error.code}: {detail}") from error
            except (urllib.error.URLError, TimeoutError):
                time.sleep(BUSY_WAIT)

        raise Refused(f"PixelLab stayed busy for {method} {path}")


def fetch_picture(url: str) -> bytes:
    parts = urlparse(url)
    host = parts.hostname or ""

    if parts.scheme != "https" or not (host == PICTURE_DOMAIN or host.endswith(f".{PICTURE_DOMAIN}")):
        raise Refused(f"picture link on an unknown host: {url[:80]}")

    # The picture host refuses Python's default User-Agent with a 403.
    request = urllib.request.Request(url, headers={"User-Agent": "pixel-data/0.1"})

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise Refused(f"picture download failed ({error.code}); run again to retry") from error


def load_plan(path: Path) -> tuple[dict, list[dict]]:
    plan = json.loads(path.read_text())

    return plan["defaults"], plan["characters"]


def request_body(defaults: dict, entry: dict) -> dict:
    size = entry.get("size", defaults["size"])

    return {
        "description": entry["description"],
        "name": entry["id"],
        "image_size": {"width": size, "height": size},
        "n_directions": entry.get("directions", defaults["directions"]),
        "view": entry.get("view", defaults["view"]),
        "outline": entry.get("outline", defaults["outline"]),
        "detail": entry.get("detail", defaults["detail"]),
        "no_background": True,
    }


def is_done(folder: Path) -> bool:
    return (folder / CHARACTER_FILE).is_file()


def to_make(source_dir: Path, characters: list[dict], limit: int) -> list[dict]:
    # A character with a job.json is paid for already: finish it before starting new ones.
    started = [entry for entry in characters if not is_done(source_dir / entry["id"]) and (source_dir / entry["id"] / JOB_FILE).is_file()]
    fresh = [entry for entry in characters if not is_done(source_dir / entry["id"]) and entry not in started]

    return started + fresh[: max(0, limit - len(started))]


def start_job(api: Api, folder: Path, body: dict) -> dict:
    job_file = folder / JOB_FILE

    if job_file.is_file():
        return json.loads(job_file.read_text())

    answer = api.call("POST", "/create-character-v3", body)
    job = {
        "background_job_id": answer["background_job_id"],
        "character_id": answer["character_id"],
        "usage": answer.get("usage"),
        "submitted_at": now(),
    }

    folder.mkdir(parents=True, exist_ok=True)
    job_file.write_text(json.dumps(job, indent=2))

    return job


def wait_for(api: Api, job_id: str, sleep: Callable[[float], None]) -> dict:
    waited = 0
    while waited < WAIT_LIMIT:
        try:
            job = api.call("GET", f"/background-jobs/{job_id}")
        except Refused as error:
            # PixelLab deletes a job some time after it ends; the character itself stays.
            if str(error).startswith("404"):
                return {"status": "gone"}
            raise

        if job["status"] == "completed":
            return job
        if job["status"] == "failed":
            detail = (job.get("last_response") or {}).get("detail", "no reason given")
            raise Refused(f"job failed: {detail}")

        sleep(POLL_SECONDS)
        waited += POLL_SECONDS

    raise Refused(f"job {job_id} took longer than {WAIT_LIMIT // 60} minutes; run again to keep waiting")


def save_pictures(folder: Path, urls: dict, fetch: Callable[[str], bytes]) -> dict:
    files = {}
    (folder / "rotations").mkdir(parents=True, exist_ok=True)

    for direction, url in sorted(urls.items()):
        if not url:
            continue

        relative = f"rotations/{direction}.png"
        (folder / relative).write_bytes(fetch(url))
        files[direction] = relative

    return files


def make_character(api: Api, folder: Path, defaults: dict, entry: dict, fetch=fetch_picture, sleep=time.sleep) -> dict:
    body = request_body(defaults, entry)
    job = start_job(api, folder, body)
    finished = wait_for(api, job["background_job_id"], sleep)
    info = api.call("GET", f"/characters/{job['character_id']}")

    if finished["status"] == "gone" and info.get("status", "completed") != "completed":
        raise Refused(f"the job is gone and the character is {info.get('status')}")
    files = save_pictures(folder, info.get("rotation_urls") or {}, fetch)

    if not files:
        raise Refused("the character came back with no pictures")

    record = {
        **entry,
        "settings": body,
        "character_id": job["character_id"],
        "size": info.get("size"),
        "view": info.get("view"),
        "files": files,
        "usage": finished.get("usage") or job.get("usage"),
        "made_at": now(),
    }
    # Written last: its presence means every picture is on disk.
    (folder / CHARACTER_FILE).write_text(json.dumps(record, indent=2))

    return record


def note_failure(source_dir: Path, entry: dict, reason: str) -> None:
    with (source_dir / FAILED_FILE).open("a") as handle:
        handle.write(json.dumps({"id": entry["id"], "reason": reason, "at": now()}) + "\n")


def show_balance(api: Api) -> None:
    balance = api.call("GET", "/balance")
    subscription = balance.get("subscription") or {}
    credits = (balance.get("credits") or {}).get("usd")

    print(
        f"  balance: {subscription.get('generations')} of {subscription.get('total')} generations left"
        f" ({subscription.get('plan')}, {subscription.get('status')}), credits ${credits}"
    )


def gather_pixellab(source: Source, layout: Layout, plan_path: Path, env_file: Path, limit: int, parallel: int, api: Api | None = None, skip: int = 0) -> dict:
    api = api or Api(read_token(env_file))
    source_dir = layout.source_dir(source)
    source_dir.mkdir(parents=True, exist_ok=True)

    defaults, characters = load_plan(plan_path)
    # skip lets a second run take a later part of the plan, so two runs never share a character.
    todo = to_make(source_dir, characters[skip:], limit)
    done_before = sum(is_done(source_dir / entry["id"]) for entry in characters)

    show_balance(api)
    print(f"  {done_before} of {len(characters)} made before; making {len(todo)} now, {parallel} at a time")

    made, failed, stop = 0, 0, None

    def one(entry: dict) -> None:
        nonlocal made, failed, stop
        if stop:
            return

        try:
            make_character(api, source_dir / entry["id"], defaults, entry, fetch=fetch_picture, sleep=time.sleep)
            made += 1
            print(f"  made {entry['id']} ({made + failed} of {len(todo)})", flush=True)
        except Refused as error:
            failed += 1
            note_failure(source_dir, entry, str(error))
            print(f"  failed {entry['id']}: {error}", flush=True)
        except Stop as error:
            stop = str(error)

    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        list(pool.map(one, todo))

    if stop:
        print(f"  stopped: {stop}")
    show_balance(api)

    summary = {"made": made, "failed": failed, "stopped": stop, "total_made": done_before + made, "planned": len(characters)}
    (source_dir / "_source.json").write_text(json.dumps({"id": source.id, "gathered_at": now(), **summary}, indent=2))

    return summary
