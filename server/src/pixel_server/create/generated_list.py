from pathlib import Path, PurePosixPath

from pixel_data.dashboard import studio

from pixel_server.library.urls import file_url

# The first generations were drawn before the sprite size could be chosen, at 64 px.
FIRST_SPRITE = 64


def generated_list(data: Path) -> dict:
    # A folder with no sheet yet is still being drawn, or its job failed: nothing to show.
    items = [item for item in studio.read_generated(data) if item["sheets"]]

    return {"items": [generated_entry(item) for item in items]}


def generated_entry(item: dict) -> dict:
    folder = item["folder"]
    sheets = [
        {"label": f"Character {number}", "src": file_url("generated", f"{folder}/{sheet}")}
        for number, sheet in enumerate(item["sheets"], start=1)
    ]

    return {
        "folder": folder,
        "prompt": item.get("prompt") or folder,
        "createdAt": item.get("created_at", ""),
        "sprite": item.get("sprite", FIRST_SPRITE),
        "facing": item.get("facing", "front"),
        "drawWith": lora_label(item.get("create_lora")),
        "drawingModel": item.get("front_model", ""),
        "turnWith": lora_label(item.get("lora")),
        "turningModel": item.get("turn_model", "") if item.get("lora") else "",
        "sheets": sheets,
    }


# "../dataset/data/runs/rotate-v2/final" reads as "rotate-v2 · final", as the form lists it.
def lora_label(path: str | None) -> str:
    if not path:
        return ""

    parts = PurePosixPath(path).parts

    if "runs" not in parts[:-1]:
        return parts[-1]

    run = parts[parts.index("runs") + 1]

    return run if run == parts[-1] else f"{run} · {parts[-1]}"
