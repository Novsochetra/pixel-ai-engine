import re
from pathlib import Path

from pixel_data.dashboard import animate_page as animate

from pixel_server.library.urls import file_url

# pixel-train names a clip s<seed>-<view>-<action>, or s<seed>-<action> for a PNG of your own.
CLIP_ID = re.compile(r"s(\d+)-(?:(front|left|back|right)-)?(.+)")


def animated_list(data: Path) -> dict:
    return {"runs": [run_entry(run) for run in animate.read_animated(data)[: animate.GALLERY]]}


def run_entry(run: dict) -> dict:
    folder = run["folder"]

    return {
        "folder": folder,
        "source": Path(run.get("source", folder)).name,
        "subject": run.get("subject", ""),
        "createdAt": run.get("created_at", ""),
        "size": run.get("size"),
        "frames": run.get("frames"),
        "openEnd": run.get("same_end") is False,
        "clips": [clip_entry(folder, clip) for clip in run["clips"]],
    }


def clip_entry(folder: str, clip: dict) -> dict:
    clip_id = clip["id"]
    match = CLIP_ID.fullmatch(clip_id)

    return {
        "id": clip_id,
        "seed": int(match[1]) if match else clip.get("seed", 0),
        "view": match[2] if match else None,
        "action": match[3] if match else clip_id,
        "kept": clip.get("kept", 0),
        "used": clip.get("used"),
        "gif": file_url("animated", f"{folder}/{clip_id}.gif"),
        "raw": file_url("animated", f"{folder}/{clip_id}-raw.gif"),
        "sheet": file_url("animated", f"{folder}/{clip_id}-sheet.png"),
    }
