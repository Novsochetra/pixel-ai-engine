from pathlib import Path

from pixel_data.dashboard import animate, studio
from pixel_data.dashboard.studio import PROMPT_LENGTH

# studio.generate_job checks these; the form shows the same limits before it sends.
POSE_LENGTH = 100
CHARACTERS = {"min": 1, "max": 8, "default": 2}
DEFAULT_SPRITE = 128
DEFAULT_MODEL = "flux2-klein-4b"
# pixel-train's own default, for a run.json that names no model.
TRAINED_ON = "flux2-klein-base-4b"


def choices(labels: dict) -> list[dict]:
    return [{"value": value, "label": label} for value, label in labels.items()]


def form_options() -> dict:
    return {
        "models": choices(studio.MODELS),
        "sprites": [{"value": str(size), "label": f"{size} × {size}"} for size in studio.SPRITES],
        "facing": choices(studio.FACING),
        "promptLength": PROMPT_LENGTH,
        "poseLength": POSE_LENGTH,
        "characters": CHARACTERS,
        "largestUpload": animate.LARGEST_UPLOAD,
        "uploadLimit": animate.UPLOAD_LIMIT,
        "defaults": {"sprite": str(DEFAULT_SPRITE), "model": DEFAULT_MODEL, "facing": "front"},
    }


# A LoRA draws best on the model it learnt on, so the form picks that model with it. A create
# LoRA from before side views learnt the front only.
def lora_list(data: Path, task: str) -> dict:
    settings = {run["name"]: run["settings"] for run in studio.read_runs(data)}
    loras = []
    for value, label in studio.lora_options(data, task):
        trained = settings.get(value.split("/")[1], {})
        lora = {"value": value, "label": label, "model": trained.get("model", TRAINED_ON)}
        loras.append(lora | ({"views": trained.get("views", ["front"])} if task == "create" else {}))

    return {"loras": loras}
