from pathlib import Path

from pixel_data.dashboard import animate_page, studio

from pixel_server.create.generated_list import FIRST_SPRITE, lora_label
from pixel_server.library.urls import file_url


# Every character a rotate LoRA turned, by Rotate or by Generate, newest first.
def rotated_list(data: Path) -> dict:
    turned = {item["folder"]: item for item in studio.read_generated(data) if item.get("lora")}
    found = [
        character_entry(turned[made["folder"]], seed, views)
        for made in animate_page.characters(data)
        if made["folder"] in turned
        for seed, views in made["sprites"].items()
        if len(views) > 1
    ]

    return {"characters": found[: studio.GALLERY]}


def character_entry(item: dict, seed: int, views: list[str]) -> dict:
    folder = item["folder"]
    source = item.get("rotated_from")

    return {
        "key": f"{folder}/s{seed}",
        "folder": folder,
        "seed": seed,
        "prompt": item.get("prompt") or folder,
        "createdAt": item.get("created_at", ""),
        "sprite": item.get("sprite", FIRST_SPRITE),
        "rotatedFrom": Path(source).name if source else "",
        "turnWith": lora_label(item.get("lora")),
        "turningModel": item.get("turn_model", ""),
        "views": [{"label": view.capitalize(), "src": file_url("generated", f"{folder}/s{seed}-{view}.png")}
                  for view in views],
    }
