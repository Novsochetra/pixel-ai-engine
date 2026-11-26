import json
import re
from pathlib import Path

from pixel_data.dashboard.invalid import Invalid
from pixel_data.dashboard.train_data import more_exports, repeat_args, trainable_sources


MODELS = {"flux2-klein-4b": "fast (4 steps, ~40 s a view)", "flux2-klein-base-4b": "base (28 steps, ~6 min a view)"}
SPRITES = (64, 96, 128)
SIZES = (256, 512)
# How the character is drawn: from the front and turned, or from the side and flipped.
FACING = {"front": "front, then turned to left, back, right", "side": "side, facing right (left is its mirror)"}
TASKS = {"rotate": "rotate: turn a front view", "create": "create: draw a front view from text"}
NAME = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
GALLERY = 40


# Reading what is on disk


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def read_log(path: Path) -> list[dict]:
    rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue

    # A resumed run logs the steps after its last checkpoint again; the later line wins.
    by_step = {row["step"]: row for row in rows if "step" in row}

    return [by_step[step] for step in sorted(by_step)]


def checkpoints(run: Path) -> list[str]:
    folder = run / "checkpoints"
    done = sorted(path.name for path in folder.glob("step-*") if (path / "state.json").is_file()) if folder.is_dir() else []

    return done


def read_runs(data: Path) -> list[dict]:
    runs = []
    for path in sorted((data / "runs").glob("*/run.json")):
        folder = path.parent
        info = read_json(path)
        rows = read_log(folder / "log.jsonl")
        settings = info.get("settings", {})
        last = rows[-1] if rows else {}
        runs.append({
            "name": folder.name,
            "settings": settings,
            "created_at": info.get("created_at", ""),
            "rows": rows,
            "step": last.get("step", 0),
            "steps": settings.get("steps", 0),
            "seconds_per_step": last.get("seconds_per_step"),
            "val": [(row["step"], row["val_loss"]) for row in rows if "val_loss" in row],
            "checkpoints": checkpoints(folder),
            "final": (folder / "final" / "pytorch_lora_weights.safetensors").is_file(),
        })

    return sorted(runs, key=lambda run: run["created_at"], reverse=True)


def task_of(run: dict) -> str:
    return run["settings"].get("task", "rotate")


def lora_options(data: Path, task: str | None = None) -> list[tuple[str, str]]:
    """(value, label) for every LoRA a job may load: each run's final one and its last checkpoints."""
    options = []
    for run in read_runs(data):
        if task and task_of(run) != task:
            continue
        if run["final"]:
            options.append((f"runs/{run['name']}/final", f"{run['name']} · final"))
        for name in reversed(run["checkpoints"][-5:]):
            options.append((f"runs/{run['name']}/checkpoints/{name}", f"{run['name']} · {name}"))

    return options


def read_generated(data: Path) -> list[dict]:
    items = []
    for path in (data / "generated").glob("*/generated.json"):
        info = read_json(path)
        sheets = sorted(sheet.name for sheet in path.parent.glob("s*-sheet.png"))
        items.append({**info, "folder": path.parent.name, "sheets": sheets})

    return sorted(items, key=lambda item: item.get("created_at", ""), reverse=True)


def exports(data: Path) -> list[str]:
    return sorted(path.parent.name for path in (data / "exports").glob("*/characters.jsonl"))


# Checking form values and turning them into pixel-train arguments


def one_of(value: str, allowed, what: str) -> str:
    if value not in [str(item) for item in allowed]:
        raise Invalid(f"Pick a {what} from the list.")

    return value


def number(value: str, low: int, high: int, what: str) -> int:
    if not value.strip().isdigit() or not low <= int(value) <= high:
        raise Invalid(f"{what} must be a whole number from {low} to {high}.")

    return int(value)


def generate_job(data: Path, form: dict) -> tuple[str, list[str]]:
    prompt = " ".join(form.get("prompt", "").split())
    if not prompt or len(prompt) > 300:
        raise Invalid("Write what to draw, in at most 300 characters.")

    seeds = number(form.get("seeds", "2"), 1, 8, "Characters")
    sprite = one_of(form.get("sprite", "128"), SPRITES, "sprite size")
    model = one_of(form.get("turn_model", "flux2-klein-4b"), MODELS, "turning model")
    front = one_of(form.get("front_model", "flux2-klein-4b"), MODELS, "drawing model")
    args = ["generate", prompt, "--seeds", str(seeds), "--sprite", sprite, "--turn-model", model, "--front-model", front]
    pose = " ".join(form.get("pose", "").split())
    if len(pose) > 100:
        raise Invalid("Write the pose in at most 100 characters.")
    if pose:
        args += ["--pose", pose]
    facing = one_of(form.get("facing", "front"), list(FACING), "facing")

    create = form.get("create_lora", "")
    if create and pose and pose.lower() != "standing":
        raise Invalid('A create LoRA draws only standing sprites. For this pose, set "Draw with" to none.')
    if create and facing == "side":
        raise Invalid('A create LoRA draws only front views. For a side view, set "Draw with" to none.')
    if facing == "side":
        # The side is drawn from the text and flipped for the left; nothing is turned.
        return f"Generate: {prompt}", [*args, "--facing", "side"]
    if create:
        one_of(create, [value for value, _ in lora_options(data, "create")], "create model")
        args += ["--create-lora", str(data.resolve() / create)]
    lora = form.get("lora", "")
    if lora:
        one_of(lora, [value for value, _ in lora_options(data, "rotate")], "trained model")
        args += ["--lora", str(data.resolve() / lora)]

    return f"Generate: {prompt}", args


def train_job(data: Path, form: dict) -> tuple[str, list[str]]:
    name = form.get("name", "").strip()
    if not NAME.match(name):
        raise Invalid("The run name may have letters, numbers, - and _, up to 40.")
    if (data / "runs" / name).exists():
        raise Invalid(f"There is already a run called {name}. Resume it, or pick another name.")

    known = exports(data)
    export = one_of(form.get("export", ""), known, "export")
    task = one_of(form.get("task", "rotate"), TASKS, "task")
    model = one_of(form.get("model", "flux2-klein-base-4b"), MODELS, "model")
    size = one_of(form.get("size", "256"), SIZES, "size")
    steps = number(form.get("steps", "2000"), 1, 50000, "Steps")
    more = more_exports(form, task, export, known)
    chosen = sorted(set(form.get("sources_list", [])))
    available = sorted({source for folder in [export, *more] for source in trainable_sources(data, folder)})
    if not chosen or any(source not in available for source in chosen):
        raise Invalid("Pick at least one source.")

    args = ["train", "--name", name, "--task", task, "--export", export, "--model", model, "--size", size,
            "--steps", str(steps)]
    if more:
        args += ["--more-exports", *more]
    if chosen != available:
        args += ["--sources", *chosen]
    args += repeat_args(form, chosen)

    return f"Train {name}: {steps} steps", args


def find_run(data: Path, name: str) -> dict:
    run = next((run for run in read_runs(data) if run["name"] == name), None)
    if run is None:
        raise Invalid("No such run.")

    return run


def resume_job(data: Path, form: dict) -> tuple[str, list[str]]:
    run = find_run(data, form.get("run", ""))
    steps = number(form.get("steps", ""), run["step"] + 1, 50000, "Steps")
    settings = run["settings"]

    # The same settings as the run had, so it goes on with what it learnt.
    args = ["train", "--name", run["name"], "--resume", "--task", task_of(run), "--steps", str(steps)]
    for flag, key in (("--export", "export"), ("--model", "model"), ("--size", "size"), ("--rank", "rank"),
                      ("--learning-rate", "learning_rate"), ("--accumulate", "accumulate"), ("--every", "every"),
                      ("--val", "val_count"), ("--seed", "seed"), ("--more-repeat", "more_repeat")):
        if key in settings:
            args += [flag, str(settings[key])]
    if settings.get("sources"):
        args += ["--sources", *settings["sources"]]
    # Without these a create run goes on with less data than it started with.
    if settings.get("more_exports"):
        args += ["--more-exports", *settings["more_exports"]]
    if settings.get("repeat"):
        args += ["--repeat", *(f"{source}={times:g}" for source, times in settings["repeat"])]

    return f"Resume {run['name']} to {steps} steps", args


def tryout_job(data: Path, form: dict) -> tuple[str, list[str]]:
    run = find_run(data, form.get("run", ""))
    if task_of(run) != "rotate":
        raise Invalid("A create run is tried on the Generate page.")
    lora = one_of(form.get("lora", ""), [value for value, _ in lora_options(data) if value.startswith(f"runs/{run['name']}/")],
                  "checkpoint")
    model = one_of(form.get("model", "flux2-klein-4b"), MODELS, "model")
    count = number(form.get("rotate", "4"), 1, 20, "Test characters")
    point = lora.rsplit("/", 1)[-1]
    short = "fast" if model == "flux2-klein-4b" else "base"
    name = f"{run['name']}-{point}-{short}"
    if (data / "tryouts" / name).exists():
        name += "-again"

    args = ["tryout", "--models", model, "--lora", str(data.resolve() / lora), "--seeds", "1",
            "--rotate", str(count), "--no-create", "--name", name]

    return f"Try {run['name']} {point} on the {short} model", args
