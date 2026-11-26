from pathlib import Path

from pixel_data.dashboard import studio

# studio.generate_job checks these; the form shows the same limits before it sends.
PROMPT_LENGTH = 300
POSE_LENGTH = 100
CHARACTERS = {"min": 1, "max": 8, "default": 2}
DEFAULT_SPRITE = 128
DEFAULT_MODEL = "flux2-klein-4b"


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
        "defaults": {"sprite": str(DEFAULT_SPRITE), "model": DEFAULT_MODEL, "facing": "front"},
    }


def lora_list(data: Path, task: str) -> dict:
    return {"loras": [{"value": value, "label": label} for value, label in studio.lora_options(data, task)]}
