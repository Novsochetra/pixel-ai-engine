from pathlib import Path

from pixel_data.dashboard.animate_page import GENERATED, characters, uploads
from pixel_data.dashboard.studio import MODELS, SPRITES, Invalid, lora_options, one_of

# The views a rotate LoRA learnt to turn a front view to, in pixel-train's order.
TURNED = ("left", "back", "right")
DEFAULT_SPRITE = "128"
DEFAULT_MODEL = "flux2-klein-4b"


def upload_source(data: Path, source: str) -> tuple[Path, list[str], str]:
    path = data / one_of(source, [f"uploads/{name}" for name in uploads(data)], "uploaded picture")

    return path, [], path.stem


# The same sources as Animate's, as long as the character has a front view to turn.
def made_source(data: Path, source: str) -> tuple[Path, list[str], str]:
    known = {item["folder"]: item for item in characters(data)}
    match = GENERATED.fullmatch(source)
    folder = one_of(match[1] if match else source, known, "character")
    sprites = known[folder]["sprites"]
    seed = int(match[2]) if match and match[2] else next(iter(sprites))

    if "front" not in sprites.get(seed, []):
        raise Invalid(f"{folder} has no front view for s{seed} to turn.")

    return data / "generated" / folder, ["--seeds", str(seed)], f"{folder} s{seed}"


def turned_views(chosen: list[str]) -> list[str]:
    if not chosen or any(view not in TURNED for view in chosen):
        raise Invalid("Pick at least one view to turn to: left, back or right.")

    return [view for view in TURNED if view in chosen]


def rotate_job(data: Path, form: dict) -> tuple[str, list[str]]:
    source = form.get("source", "")
    is_upload = source.startswith("uploads/")
    target, seeds, stem = upload_source(data, source) if is_upload else made_source(data, source)

    loras = [value for value, _ in lora_options(data, "rotate")]
    lora = one_of(form.get("lora", ""), loras, "rotate LoRA")
    model = one_of(form.get("turn_model", DEFAULT_MODEL), MODELS, "turning model")
    sprite = one_of(form.get("sprite", DEFAULT_SPRITE), SPRITES, "sprite size")
    views = turned_views(form.get("views_list", list(TURNED)))

    args = ["rotate", str(target.resolve()), *seeds, "--lora", str(data.resolve() / lora), "--turn-model", model,
            "--sprite", sprite, "--views", *views]

    return f"Rotate {stem}: {len(views)} view{'s' if len(views) > 1 else ''}", args
