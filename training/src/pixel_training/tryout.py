import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from PIL import Image

from pixel_training.models import Generate
from pixel_training.pixelate import blow_up, pixelate

GENERATE_SIZE = 1024
SPRITE_SIZE = 64


@dataclass
class Plan:
    folder: Path
    create: list[dict]
    rotate: list[dict]
    seeds: list[int]
    timings: dict = field(default_factory=dict)


def create_jobs(prompts: dict) -> list[dict]:
    template = prompts["create"]["template"]

    return [{"id": f"p{index:02d}", "prompt": template.format(subject=subject)} for index, subject in enumerate(prompts["create"]["subjects"])]


def rotate_jobs(export: Path, prompts: dict, count: int, seed: int = 7) -> list[dict]:
    if count == 0 or not (export / "characters.jsonl").exists():
        return []

    tests = [json.loads(line) for line in (export / "characters.jsonl").read_text().splitlines()]
    tests = [entry for entry in tests if entry["split"] == "test"]
    chosen = random.Random(seed).sample(tests, min(count, len(tests)))

    return [
        {"id": f"r{index:02d}-{view}", "character": entry["character"], "view": view, "prompt": instruction,
         "front": export / entry["views"]["front"], "truth": export / entry["views"][view]}
        for index, entry in enumerate(chosen)
        for view, instruction in prompts["rotate"].items()
    ]


def save_pair(image: Image.Image, folder: Path, stem: str) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").resize((256, 256), Image.LANCZOS).save(folder / f"{stem}-raw.png")
    pixelate(image, SPRITE_SIZE).save(folder / f"{stem}-pixel.png")

    return {"raw": f"{folder.name}/{stem}-raw.png", "pixel": f"{folder.name}/{stem}-pixel.png"}


def run_create(plan: Plan, model: str, generate: Generate) -> dict:
    outputs = {}
    for job in plan.create:
        for seed in plan.seeds:
            image = generate(job["prompt"], None, seed)
            outputs[f"{job['id']}-s{seed}"] = save_pair(image, plan.folder / model, f"{job['id']}-s{seed}")

    return outputs


def run_rotate(plan: Plan, model: str, generate: Generate) -> dict:
    outputs = {}
    for job in plan.rotate:
        reference = blow_up(Image.open(job["front"]), GENERATE_SIZE)
        image = generate(job["prompt"], reference, plan.seeds[0])
        outputs[job["id"]] = save_pair(image, plan.folder / model, job["id"])

    return outputs


def run_model(plan: Plan, model: str, load: Callable[[], Generate]) -> dict:
    started = time.monotonic()
    try:
        generate = load()
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"}

    loaded = time.monotonic()
    result = {"create": run_create(plan, model, generate), "rotate": run_rotate(plan, model, generate)}

    images = len(plan.create) * len(plan.seeds) + len(plan.rotate)
    result["load_seconds"] = round(loaded - started, 1)
    result["seconds_per_image"] = round((time.monotonic() - loaded) / max(1, images), 1)

    return result


def copy_references(plan: Plan) -> list[dict]:
    references = plan.folder / "references"
    references.mkdir(parents=True, exist_ok=True)

    rows = []
    for job in plan.rotate:
        for kind in ("front", "truth"):
            Image.open(job[kind]).save(references / f"{job['id']}-{kind}.png")

        rows.append({"id": job["id"], "character": job["character"], "view": job["view"],
                     "front": f"references/{job['id']}-front.png", "truth": f"references/{job['id']}-truth.png"})

    return rows


def write_results(plan: Plan, name: str, models: dict, extra: dict) -> Path:
    results = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **extra,
        "seeds": plan.seeds,
        "create": [{"id": job["id"], "prompt": job["prompt"]} for job in plan.create],
        "rotate": copy_references(plan),
        "models": models,
    }

    path = plan.folder / "results.json"
    path.write_text(json.dumps(results, indent=2))

    return path
