import io
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from pixel_data.dashboard.studio import Invalid, one_of, read_generated, read_json

VIEWS = ("front", "left", "back", "right")
# idle, walk and attack have their own words in pixel-train; any other action is used as written.
DEFAULT_ACTIONS = "idle\nwalk"
MOST_ACTIONS = 8
LONGEST_ACTION = 200
SIZES = {"384": "384 px (faster)", "512": "512 px"}
FRAMES = {"17": "17 frames (~1 s)", "33": "33 frames (~2 s)"}
# Minutes a clip takes on an M1 Max (32 GB), by size and frames; loading the models comes on top.
MINUTES = {("384", "33"): 11, ("512", "33"): 15, ("384", "17"): 6, ("512", "17"): 8}
LARGEST_UPLOAD = 2048
UPLOAD_LIMIT = 10_000_000
GALLERY = 30
SPRITE = re.compile(r"^s(\d+)-(front|left|back|right)\.png$")
# generated/<folder>/s<seed>, or generated/<folder> for its first character.
GENERATED = re.compile(r"generated/([^/]+)(?:/s(\d+))?")


# Reading what is on disk


def characters(data: Path) -> list[dict]:
    """Every generated character with the seeds and views it has sprites for."""
    found = []
    for item in read_generated(data):
        sprites = {}
        for path in (data / "generated" / item["folder"]).glob("s*-*.png"):
            match = SPRITE.match(path.name)
            if match:
                sprites.setdefault(int(match[1]), set()).add(match[2])
        if sprites:
            found.append({"folder": item["folder"], "prompt": item.get("prompt", item["folder"]),
                          "sprites": {seed: sorted(views, key=VIEWS.index) for seed, views in sorted(sprites.items())}})

    return found


def uploads(data: Path) -> list[str]:
    return sorted((path.name for path in (data / "uploads").glob("*.png")), reverse=True)


def read_animated(data: Path) -> list[dict]:
    runs = []
    for path in (data / "animated").glob("*/animated.json"):
        info = read_json(path)
        clips = [clip for clip in info.get("clips", []) if (path.parent / f"{clip.get('id')}.gif").is_file()]
        runs.append({**info, "folder": path.parent.name, "clips": clips})

    return sorted(runs, key=lambda run: run.get("created_at", ""), reverse=True)


# Saved again with Pillow, so the job reads a clean PNG the dashboard made, not the bytes sent.
def save_upload(data: Path, filename: str, body: bytes) -> Path:
    """The uploaded picture as a clean PNG under data/uploads/, or Invalid if it is not a picture."""
    try:
        picture = Image.open(io.BytesIO(body))
        picture.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise Invalid("The file is not a picture. Upload a PNG.") from None
    if max(picture.size) > LARGEST_UPLOAD:
        raise Invalid(f"The picture is {picture.width} x {picture.height}. Upload one of at most {LARGEST_UPLOAD} pixels a side.")

    stem = re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-")[:40] or "upload"
    folder = data / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{datetime.now():%Y%m%d-%H%M%S}-{stem}.png"
    picture.convert("RGBA").save(path)

    return path


# Checking the form and turning it into pixel-train arguments


def read_actions(text: str) -> list[str]:
    """One action a line, spaces tidied, each only once."""
    actions = {}
    for line in text.splitlines():
        action = " ".join(line.split())
        if action:
            actions.setdefault(action.lower(), action)
    if not actions:
        raise Invalid("Say at least one action, for example: walk, or flaps its wings.")
    if len(actions) > MOST_ACTIONS:
        raise Invalid(f"Give at most {MOST_ACTIONS} actions at a time.")
    if any(len(action) > LONGEST_ACTION for action in actions.values()):
        raise Invalid(f"Keep each action to at most {LONGEST_ACTION} characters.")

    return list(actions.values())


def animate_job(data: Path, form: dict) -> tuple[str, list[str]]:
    actions = read_actions(form.get("actions", ""))
    size = one_of(form.get("size", "384"), SIZES, "video size")
    frames = one_of(form.get("frames", "33"), FRAMES, "length")
    subject = " ".join(form.get("subject", "").split())
    if len(subject) > 300:
        raise Invalid("Keep the description to at most 300 characters.")

    upload = form.get("files", {}).get("image")
    source = form.get("source", "")
    if source == "upload" or source.startswith("uploads/"):
        if not subject:
            raise Invalid("Say what the picture shows, for example: a knight in grey armour, empty hands.")
        if source.startswith("uploads/"):
            path = data / one_of(source, [f"uploads/{name}" for name in uploads(data)], "uploaded picture")
        elif upload:
            path = save_upload(data, *upload)
        else:
            raise Invalid("Choose a PNG to upload.")
        target, stem, views = str(path.resolve()), path.stem, [None]
        args = ["animate", target, "--seeds", "0"]
    else:
        known = {item["folder"]: item for item in characters(data)}
        match = GENERATED.fullmatch(source)
        folder = one_of(match[1] if match else source, known, "character")
        sprites = known[folder]["sprites"]
        seed = int(match[2]) if match and match[2] else next(iter(sprites))
        have = sprites.get(seed)
        if have is None:
            raise Invalid(f"{folder} has no character s{seed}.")
        views = form.get("views_list", [])
        if not views or any(view not in have for view in views):
            raise Invalid(f"Pick at least one view that s{seed} has: {', '.join(have)}.")
        target, stem = str((data / "generated" / folder).resolve()), folder
        args = ["animate", target, "--views", *views, "--seeds", str(seed)]

    name = f"{datetime.now():%Y%m%d-%H%M%S}-{stem}"[:60]
    args += ["--actions", *actions, "--size", size, "--frames", frames, "--name", name]
    if subject:
        args += ["--subject", subject]

    clips = len(views) * len(actions)

    return f"Animate {stem}: {clips} clip{'s' if clips > 1 else ''}", args
