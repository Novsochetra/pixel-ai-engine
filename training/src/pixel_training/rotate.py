import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image

from pixel_training.animate import square
from pixel_training.generate import sheets, turn, write_info
from pixel_training.models import PRESETS, Generate
from pixel_training.pixelate import blow_up, pixelate

TURNED = ("left", "back", "right")
FRONT = re.compile(r"^s(\d+)-front\.png$")


@dataclass(frozen=True)
class Turning:
    instructions: dict[str, str]
    size: int
    sprite: int


def generated_fronts(folder: Path, seeds: list[int] | None) -> list[Path]:
    if not (folder / "generated.json").is_file():
        raise SystemExit(f"No character at {folder}. Make one with `uv run pixel-train generate` first, or give a PNG file.")

    found = {int(match[1]): path for path in folder.glob("s*-front.png") if (match := FRONT.match(path.name))}
    missing = sorted(set(seeds or []) - set(found))

    if missing or not found:
        raise SystemExit(f"{folder.name} has no front view for seeds {missing or 'any'}.")

    return [found[seed] for seed in sorted(seeds or found)]


# The new folder keeps each front's seed, so s3 stays s3 and is turned with the same noise seed.
def copy_fronts(folder: Path, fronts: list[Path]) -> list[Path]:
    folder.mkdir(parents=True)

    for front in fronts:
        raw = front.with_name(front.name.replace("-front.png", "-front-raw.png"))

        for path in (front, raw):
            if path.is_file():
                shutil.copyfile(path, folder / path.name)

    return [folder / front.name for front in fronts]


# A picture bigger than the sprite is snapped to it, as generate snaps the model's picture; a
# sprite already that size or smaller is kept as it was drawn.
def upload_front(folder: Path, picture: Path, sprite: int) -> list[Path]:
    folder.mkdir(parents=True)
    image = square(Image.open(picture))

    image.save(folder / "s0-front-raw.png")
    if image.width > sprite:
        image = pixelate(blow_up(image, image.width), sprite)

    image.save(folder / "s0-front.png")

    return [folder / "s0-front.png"]


def source_path(source: Path, data: Path) -> Path:
    return source if source.exists() else data / "generated" / source


def place_fronts(folder: Path, source: Path, seeds: list[int] | None, sprite: int) -> tuple[list[Path], dict]:
    if source.is_file():
        return upload_front(folder, source, sprite), {"prompt": source.stem, "rotated_from": str(source)}

    fronts = generated_fronts(source, seeds)
    made = json.loads((source / "generated.json").read_text())

    return copy_fronts(folder, fronts), {"prompt": made.get("prompt", source.name), "rotated_from": str(source)}


def turn_fronts(folder: Path, fronts: list[Path], turner: Generate, turning: Turning) -> list[Path]:
    turn(folder, fronts, turning.instructions, turner, turning.size, turning.sprite)

    return sheets(folder, [int(FRONT.match(front.name)[1]) for front in fronts])


def folder_for(args) -> Path:
    name = args.name or f"{datetime.now():%Y%m%d-%H%M%S}-turned-{args.source.stem}"[:60]
    folder = args.data / "generated" / name

    if folder.exists():
        raise SystemExit(f"{folder} is already there. Give another --name.")

    return folder


def rotate_command(args, lora: Path, trained: dict) -> None:
    from pixel_training.models import generator_for, pick_device

    prompts = json.loads(args.prompts.read_text())
    folder = folder_for(args)
    fronts, origin = place_fronts(folder, source_path(args.source, args.data), args.seeds, args.sprite)

    model = args.turn_model or trained.get("model", "flux2-klein-base-4b")
    # As in generate: the LoRA learnt 64-pixel sprites, so a bigger sprite is turned in a bigger picture.
    size = args.turn_size or trained.get("size", 512) * args.sprite // 64
    turning = Turning({view: prompts["rotate"][view] for view in args.views}, size, args.sprite)
    print(f"== turning {len(fronts)} front views with the LoRA in {lora}: {model}, {size}px")

    turner = generator_for(PRESETS[model], pick_device(), size, lora, args.steps)
    made = turn_fronts(folder, fronts, turner, turning)
    write_info(folder, {**origin, "seeds": [int(FRONT.match(front.name)[1]) for front in fronts],
                        "sprite": args.sprite, "lora": str(lora), "turn_model": model, "size": size,
                        "views": list(args.views)})

    print(f"\nDone. Look at: {', '.join(str(path) for path in made)}")


def add_rotate_parser(commands, models: list[str]) -> None:
    rotate = commands.add_parser("rotate", help="turn front views you already have to the left, back and right views")
    rotate.add_argument("source", type=Path, help="a folder from `generate`, its name under data/generated, or a PNG")
    rotate.add_argument("--lora", type=Path, required=True, help="a rotate training run (or checkpoint), or its name")
    rotate.add_argument("--seeds", type=int, nargs="+", help="which characters of the folder (default: all)")
    rotate.add_argument("--views", nargs="+", choices=TURNED, default=list(TURNED), help="views to turn to")
    rotate.add_argument("--sprite", type=int, default=128, help="sprite size in pixels of the turned views")
    rotate.add_argument("--turn-size", type=int, help="picture size for turning (default: the LoRA's, scaled with --sprite)")
    rotate.add_argument("--turn-model", choices=models, help="the model that turns it (default: the LoRA's own)")
    rotate.add_argument("--steps", type=int, help="sampling steps for turning (default: the model's own)")
    rotate.add_argument("--prompts", type=Path, default=Path("prompts.json"))
    rotate.add_argument("--name", help="folder name under data/generated (default: <date>-turned-<source>)")
