"""Text to a character in 4 views: a model draws the front view, then the trained LoRA turns it.

The LoRA was trained to turn a front view into the left, back and right views, not to draw from
text, so the front view comes from a model without it.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from pixel_training.models import Generate
from pixel_training.pixelate import blow_up, pixelate

SPRITE = 64
VIEWS = ("front", "left", "back", "right")
SHEET_SCALE = 4


def make_fronts(folder: Path, prompt: str, seeds: list[int], generate: Generate, sprite: int = SPRITE) -> list[Path]:
    """Draw the front view once per seed; keep the raw picture and the sprite."""
    folder.mkdir(parents=True, exist_ok=True)
    fronts = []
    for seed in seeds:
        image = generate(prompt, None, seed)
        image.convert("RGB").save(folder / f"s{seed}-front-raw.png")
        pixelate(image, sprite).save(folder / f"s{seed}-front.png")
        fronts.append(folder / f"s{seed}-front.png")

    return fronts


def turn(folder: Path, fronts: list[Path], instructions: dict[str, str], generate: Generate, size: int,
         sprite: int = SPRITE) -> None:
    """Turn every front view to each view in the instructions, the way the LoRA was trained."""
    for front in fronts:
        seed = front.name.split("-")[0]
        reference = blow_up(Image.open(front), size)
        for view, instruction in instructions.items():
            image = generate(instruction, reference, int(seed[1:]))
            image.convert("RGB").save(folder / f"{seed}-{view}-raw.png")
            pixelate(image, sprite).save(folder / f"{seed}-{view}.png")


def sheets(folder: Path, seeds: list[int]) -> list[Path]:
    """One picture per seed with the views it has side by side, scaled up so it is easy to look at."""
    made = []
    for seed in seeds:
        views = [folder / f"s{seed}-{view}.png" for view in VIEWS if (folder / f"s{seed}-{view}.png").exists()]
        size = SPRITE * SHEET_SCALE  # the same on-screen size for every sprite size, so sheets compare
        sheet = Image.new("RGBA", (size * len(views), size), (255, 255, 255, 255))
        for index, path in enumerate(views):
            sprite = Image.open(path).convert("RGBA").resize((size, size), Image.NEAREST)
            sheet.alpha_composite(sprite, (index * size, 0))
        sheet.save(folder / f"s{seed}-sheet.png")
        made.append(folder / f"s{seed}-sheet.png")

    return made


def write_info(folder: Path, info: dict) -> None:
    info = {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **info}
    (folder / "generated.json").write_text(json.dumps(info, indent=2))
