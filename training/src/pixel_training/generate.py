"""Text to a character in 4 views: a model draws the front view, then the trained LoRA turns it.

The LoRA was trained to turn a front view into the left, back and right views, not to draw from
text, so the front view comes from a model without it.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from pixel_training.models import Generate
from pixel_training.pixelate import Snap, blow_up

SPRITE = 64
VIEWS = ("front", "left", "back", "right")
SHEET_SCALE = 4


def make_fronts(folder: Path, prompt: str, seeds: list[int], generate: Generate, snap: Snap = Snap(SPRITE),
                view: str = "front") -> list[Path]:
    """Draw one view (the front, or the right side) once per seed; keep the raw picture and the sprite."""
    folder.mkdir(parents=True, exist_ok=True)
    fronts = []
    for number, seed in enumerate(seeds, 1):
        print(f"{view} view {number} of {len(seeds)} (seed {seed})...", flush=True)
        image = generate(prompt, None, seed)
        image.convert("RGB").save(folder / f"s{seed}-{view}-raw.png")
        snap(image).save(folder / f"s{seed}-{view}.png")
        fronts.append(folder / f"s{seed}-{view}.png")

    return fronts


def read_reference(path: Path, size: int) -> Image.Image:
    picture = Image.open(path).convert("RGBA")
    flat = Image.new("RGBA", picture.size, (255, 255, 255, 255))
    flat.alpha_composite(picture)

    # Scaled up with hard edges here: the model's own resize would blur a small sprite.
    scale = max(1, size // max(picture.size))

    return flat.convert("RGB").resize((picture.width * scale, picture.height * scale), Image.NEAREST)


# A view drawn from text has no picture in; the reference fills that slot, so the model draws from it.
def with_reference(generate: Generate, reference: Image.Image) -> Generate:
    def draw(prompt: str, image: Image.Image | None, seed: int) -> Image.Image:
        return generate(prompt, reference if image is None else image, seed)

    return draw


def mirror(sides: list[Path]) -> list[Path]:
    """The left view of each right view: the same sprite flipped."""
    made = []
    for side in sides:
        left = side.with_name(side.name.replace("-right.png", "-left.png"))
        Image.open(side).transpose(Image.FLIP_LEFT_RIGHT).save(left)
        made.append(left)

    return made


def turn(folder: Path, fronts: list[Path], instructions: dict[str, str], generate: Generate, size: int,
         snap: Snap = Snap(SPRITE)) -> None:
    """Turn every front view to each view in the instructions, the way the LoRA was trained."""
    total, number = len(fronts) * len(instructions), 0
    for front in fronts:
        seed = front.name.split("-")[0]
        reference = blow_up(Image.open(front), size)
        for view, instruction in instructions.items():
            number += 1
            # One line per picture: a sampling progress bar on a Mac fills before the GPU is done,
            # so it says nothing about how far a slow model has got.
            started = time.monotonic()
            print(f"turning {number} of {total}: {seed} {view}...", flush=True)
            image = generate(instruction, reference, int(seed[1:]))
            print(f"  done in {time.monotonic() - started:.0f}s", flush=True)
            image.convert("RGB").save(folder / f"{seed}-{view}-raw.png")
            snap(image).save(folder / f"{seed}-{view}.png")


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
