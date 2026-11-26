import re
import shutil
from pathlib import Path

from pixel_data.dashboard.studio import Invalid

# The folders of data/ that hold what the dashboard made, each a set that is deleted whole.
KINDS = ("generated", "animated")

# The names pixel-train gives its folders: never a path, so nothing outside those folders can move.
FOLDER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")


class Busy(RuntimeError):
    pass


def folder_name(value) -> str:
    if not isinstance(value, str) or not FOLDER.match(value) or ".." in value:
        raise Invalid("Give the name of one folder, not a path.")

    return value


def made_kind(value) -> str:
    if value not in KINDS:
        raise Invalid(f"Delete only from {' or '.join(KINDS)}.")

    return value


def trash_folder(data: Path, kind: str) -> Path:
    return data / "trash" / kind


# A job that reads or writes the folder would fail halfway if it went away under it.
def in_use(kind: str, name: str, job: dict | None) -> bool:
    if not job or job["status"] != "running":
        return False

    return any(f"{kind}/{name}" in arg or arg == name for arg in job.get("args", []))


# The same folder may be deleted, made again and deleted again: each trashed copy keeps a name.
def free_name(folder: Path, name: str) -> str:
    trashed, number = name, 1

    while (folder / trashed).exists():
        number += 1
        trashed = f"{name}-{number}"

    return trashed


# Moved, not erased, so Undo can bring it back; the person empties data/trash/ when they want.
def trash_made(data: Path, kind, name, job: dict | None) -> dict:
    source = data / made_kind(kind) / folder_name(name)

    if not source.is_dir():
        raise FileNotFoundError(f"There is nothing called {name} in {kind}.")

    if in_use(kind, name, job):
        raise Busy("A running job uses it. Wait for the job, or stop it first.")

    bin_folder = trash_folder(data, kind)
    bin_folder.mkdir(parents=True, exist_ok=True)
    trashed = free_name(bin_folder, name)
    shutil.move(source, bin_folder / trashed)

    return {"folder": name, "trashed": trashed}


def restore_made(data: Path, kind, name, trashed) -> dict:
    target = data / made_kind(kind) / folder_name(name)
    source = trash_folder(data, kind) / folder_name(trashed)

    if not source.is_dir():
        raise FileNotFoundError(f"{trashed} is not in the trash any more.")

    if target.exists():
        raise Busy(f"There is a {name} again already, so the deleted one stays in the trash.")

    shutil.move(source, target)

    return {"folder": name}
