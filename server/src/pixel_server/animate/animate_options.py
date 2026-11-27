from pathlib import Path

from pixel_data.dashboard import animate

from pixel_server.create.form_options import choices
from pixel_server.library.urls import file_url

# animate_job checks these; the form shows the same limits before it sends.
SUBJECT_LENGTH = 300
DEFAULT_VIEWS = ["front", "right"]


def animate_options() -> dict:
    return {
        "views": list(animate.VIEWS),
        "sizes": choices(animate.SIZES),
        "frames": choices(animate.FRAMES),
        "minutes": [
            {"size": size, "frames": frames, "minutes": minutes} for (size, frames), minutes in animate.MINUTES.items()
        ],
        "mostActions": animate.MOST_ACTIONS,
        "longestAction": animate.LONGEST_ACTION,
        "subjectLength": SUBJECT_LENGTH,
        "largestUpload": animate.LARGEST_UPLOAD,
        "uploadLimit": animate.UPLOAD_LIMIT,
        "defaults": {"size": "384", "frames": "33", "actions": animate.DEFAULT_ACTIONS, "views": DEFAULT_VIEWS},
    }


# One choice per character: a folder holds a sprite set for each seed it drew.
def animate_sources(data: Path) -> dict:
    made = [
        made_source(item, seed, views)
        for item in animate.characters(data)
        for seed, views in item["sprites"].items()
    ]

    return {"characters": made, **upload_list(data)}


def upload_list(data: Path) -> dict:
    return {"uploads": [upload_source(name) for name in animate.uploads(data)]}


def made_source(item: dict, seed: int, views: list[str]) -> dict:
    folder = item["folder"]

    return {
        "value": f"generated/{folder}/s{seed}",
        "label": f"{item['prompt'][:70]} · s{seed}",
        "subject": item["prompt"],
        "views": views,
        "pictures": {view: file_url("generated", f"{folder}/s{seed}-{view}.png") for view in views},
    }


def upload_source(name: str) -> dict:
    return {"value": f"uploads/{name}", "label": name, "src": file_url("uploads", name)}
