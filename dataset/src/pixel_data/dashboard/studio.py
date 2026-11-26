"""The Generate and Training pages: start `pixel-train` jobs from the browser and look at what they made."""

import json
import re
from html import escape
from pathlib import Path

from pixel_data.dashboard.browse_pages import link, readable_time

MODELS = {"flux2-klein-4b": "fast (4 steps, ~40 s a view)", "flux2-klein-base-4b": "base (28 steps, ~6 min a view)"}
SPRITES = (64, 96, 128)
SIZES = (256, 512)
# How the character is drawn: from the front and turned, or from the side and flipped.
FACING = {"front": "front, then turned to left, back, right", "side": "side, facing right (left is its mirror)"}
TASKS = {"rotate": "rotate: turn a front view", "create": "create: draw a front view from text"}
NAME = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
GALLERY = 40


class Invalid(ValueError):
    """A form value the dashboard will not pass on."""


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


def export_sources(data: Path, export: str) -> list[str]:
    return sorted(read_json(data / "exports" / export / "export.json").get("sources", {}))


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

    export = one_of(form.get("export", ""), exports(data), "export")
    task = one_of(form.get("task", "rotate"), TASKS, "task")
    model = one_of(form.get("model", "flux2-klein-base-4b"), MODELS, "model")
    size = one_of(form.get("size", "256"), SIZES, "size")
    steps = number(form.get("steps", "2000"), 1, 50000, "Steps")
    chosen = form.get("sources_list", [])
    available = export_sources(data, export)
    if not chosen or any(source not in available for source in chosen):
        raise Invalid("Pick at least one source.")

    args = ["train", "--name", name, "--task", task, "--export", export, "--model", model, "--size", size,
            "--steps", str(steps)]
    if sorted(chosen) != available:
        args += ["--sources", *sorted(chosen)]

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


# Drawing the pages


def job_panel(job: dict | None, log: str, back: str) -> str:
    if job is None:
        return '<section class="job"><p class="muted">No jobs yet. Start one below.</p></section>'

    state = {"running": "check", "done": "ok", "failed": "drop", "stopped": "drop"}.get(job["status"], "check")
    stop = (f'<form method="post" action="/jobs/stop" class="inline"><input type="hidden" name="back" value="{back}"><button class="danger">Stop</button></form>'
            if job["status"] == "running" else "")
    when = escape(readable_time(job["started_at"]))
    running = "true" if job["status"] == "running" else "false"

    return f"""<section class="job" data-running="{running}">
<header><span class="outcome {state}" id="job-status">{escape(job['status'])}</span><strong>{escape(job['title'])}</strong>
<span class="muted">started {when}</span>{stop}</header>
<pre id="job-log">{escape(log) or "…"}</pre></section>"""


POLL = """<script>
(function () {
  const panel = document.querySelector('.job');
  const log = document.getElementById('job-log');
  if (log) log.scrollTop = log.scrollHeight;  // the newest lines, also for a finished job
  if (!panel || panel.dataset.running !== 'true') return;
  const status = document.getElementById('job-status');
  async function tick() {
    try {
      const reply = await fetch('/jobs/current', {cache: 'no-store'});
      const data = await reply.json();
      const atEnd = log.scrollTop + log.clientHeight >= log.scrollHeight - 8;
      log.textContent = data.log || '…';
      if (atEnd) log.scrollTop = log.scrollHeight;
      if (!data.job || data.job.status !== 'running') { location.reload(); return; }
      status.textContent = data.job.status;
    } catch (error) {}
    setTimeout(tick, 3000);
  }
  setTimeout(tick, 3000);
})();
</script>"""


def options(values, chosen: str, labels: dict | None = None) -> str:
    return "".join(
        f'<option value="{escape(str(value))}"{" selected" if str(value) == chosen else ""}>{escape((labels or {}).get(value, str(value)))}</option>'
        for value in values
    )


def message_block(message: str) -> str:
    return f'<p class="note error">{escape(message)}</p>' if message else ""


def lora_select(loras: list[tuple[str, str]], chosen: str, none: str) -> str:
    return f'<option value="">{escape(none)}</option>' + "".join(
        f'<option value="{escape(value)}"{" selected" if value == chosen else ""}>{escape(label)}</option>' for value, label in loras
    )


def generate_page(data: Path, job: dict | None, log: str, form: dict, message: str = "") -> str:
    loras = lora_options(data, "rotate")
    turn_select = lora_select(loras, form.get("lora", loras[0][0] if loras else ""), "none: front view only")
    # The plain model stays the default for drawing until you pick a create LoRA you like.
    draw_select = lora_select(lora_options(data, "create"), form.get("create_lora", ""), "none: the model as it is")

    items = []
    for item in read_generated(data)[:GALLERY]:
        sheets = "".join(
            f'<a href="{link(f"/generated/{item["folder"]}/{sheet}")}"><img class="sheet" src="{link(f"/generated/{item["folder"]}/{sheet}")}" alt="{escape(sheet)}" loading="lazy"></a>'
            for sheet in item["sheets"]
        )
        details = [f"{item.get('sprite', 64)}px", item.get("turn_model", "no turning") if item.get("lora") else
                   "side, flipped" if item.get("facing") == "side" else "front only"]
        if item.get("create_lora"):
            drawn = Path(item["create_lora"])
            details.append("drawn by " + (drawn.parent.name if drawn.name == "final" else drawn.name))
        if item.get("lora"):
            details.append(Path(item["lora"]).parent.name if Path(item["lora"]).name == "final" else Path(item["lora"]).name)
        when = escape(readable_time(item["created_at"])) if item.get("created_at") else ""
        items.append(
            f'<article class="row"><header><strong>{escape(item.get("prompt", item["folder"]))}</strong>'
            f'<span class="muted">{when} · {escape(" · ".join(details))}</span>'
            f'<a class="chip" href="{link("/animate", source=f"generated/{item["folder"]}")}">Animate</a></header>{sheets}</article>'
        )

    gallery = "".join(items) or '<p class="muted">Nothing made yet.</p>'
    prompt = escape(form.get("prompt", ""))

    return f"""<h1>Generate</h1>
{message_block(message)}{job_panel(job, log, "/generate")}
<form method="post" action="/generate" class="panel">
<label class="wide">What to draw<textarea name="prompt" rows="2" required maxlength="300" placeholder="a frog wizard with a staff">{prompt}</textarea></label>
<label class="wide">Pose<input name="pose" maxlength="100" placeholder="standing" value="{escape(form.get('pose', ''))}"></label>
<label>Facing<select name="facing">{options(list(FACING), form.get('facing', 'front'), FACING)}</select></label>
<label>Characters<input type="number" name="seeds" min="1" max="8" value="{escape(form.get('seeds', '2'))}"></label>
<label>Sprite size<select name="sprite">{options(SPRITES, form.get('sprite', '128'), {s: f'{s} x {s}' for s in SPRITES})}</select></label>
<label>Draw with<select name="create_lora">{draw_select}</select></label>
<label>Drawing model<select name="front_model">{options(MODELS, form.get('front_model', 'flux2-klein-4b'), MODELS)}</select></label>
<label>Turn with<select name="lora">{turn_select}</select></label>
<label>Turning model<select name="turn_model">{options(MODELS, form.get('turn_model', 'flux2-klein-4b'), MODELS)}</select></label>
<button>Generate</button>
<p class="muted wide">A create LoRA draws the front view from your text; a rotate LoRA turns it to the left, back and right. The pose is standing when you leave it empty. For another pose, such as flying, draw with "none": the create LoRA learned only standing sprites. For a side pose, such as a dragon flying to the right, pick Facing: side; it is drawn with no LoRA and not turned.</p>
</form>
<h2>Made so far</h2><section class="rows wide">{gallery}</section>{POLL}"""


def chart(run: dict) -> str:
    """The check score over the steps, with the training loss behind it, as a small SVG."""
    width, height, pad = 560, 150, 28
    val = run["val"]
    rows = run["rows"]
    if not rows:
        return '<p class="muted">No steps yet.</p>'

    window = 25
    smooth = []
    for index in range(0, len(rows), 5):
        chunk = rows[max(0, index - window):index + 1]
        smooth.append((rows[index]["step"], sum(row["loss"] for row in chunk) / len(chunk)))

    values = [value for _, value in smooth + val]
    low, high = min(values), max(values)
    high = high if high > low else low + 1e-6
    last = max(run["steps"], rows[-1]["step"], 1)

    def point(step, value):
        x = pad + (width - 2 * pad) * step / last
        y = pad / 2 + (height - pad * 1.5) * (high - value) / (high - low)
        return f"{x:.1f},{y:.1f}"

    loss_line = " ".join(point(step, value) for step, value in smooth)
    val_line = " ".join(point(step, value) for step, value in val)
    dots = "".join(f'<circle cx="{point(s, v).split(",")[0]}" cy="{point(s, v).split(",")[1]}" r="2.5"/>' for s, v in val)

    return f"""<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Loss over steps">
<line x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}" class="axis"/>
<text x="{pad}" y="{height - 8}" class="label">0</text><text x="{width - pad}" y="{height - 8}" class="label" text-anchor="end">{last:,} steps</text>
<text x="2" y="{pad / 2 + 4}" class="label">{high:.3f}</text><text x="2" y="{height - pad}" class="label">{low:.3f}</text>
<polyline points="{loss_line}" class="loss"/><polyline points="{val_line}" class="val"/><g class="val-dots">{dots}</g>
</svg><p class="legend"><span class="key val"></span>check score (fixed val pairs) <span class="key loss"></span>training loss, smoothed</p>"""


def run_card(data: Path, run: dict, running: bool) -> str:
    settings = run["settings"]
    model = MODELS.get(settings.get("model", ""), settings.get("model", "?"))
    sources = ", ".join(settings.get("sources") or ["all sources"])
    progress = min(100, round(100 * run["step"] / run["steps"])) if run["steps"] else 0
    val_now = f"{run['val'][-1][1]:.4f}" if run["val"] else "–"
    per_step = run["seconds_per_step"]
    left = ""
    if per_step and run["step"] < run["steps"]:
        hours = (run["steps"] - run["step"]) * per_step / 3600
        left = f" · ~{hours:.1f} h left at {per_step:.0f}s per step"

    loras = [(value, label) for value, label in lora_options(data) if value.startswith(f"runs/{run['name']}/")]
    task = task_of(run)
    disabled = " disabled" if running else ""
    next_steps = run["steps"] if run["step"] < run["steps"] else run["steps"] + 1000

    actions = f"""<form method="post" action="/training/resume" class="inline">
<input type="hidden" name="run" value="{escape(run['name'])}">
<label>to<input type="number" name="steps" min="{run['step'] + 1}" value="{next_steps}"></label><button{disabled}>Resume</button></form>"""
    if loras and task == "create":
        actions += f"""<a class="chip" href="{link('/generate', create_lora=loras[0][0])}">Try in Generate</a>"""
    elif loras:
        actions += f"""<form method="post" action="/training/tryout" class="inline">
<input type="hidden" name="run" value="{escape(run['name'])}">
<select name="lora">{"".join(f'<option value="{escape(value)}">{escape(label.split(" · ")[-1])}</option>' for value, label in loras)}</select>
<select name="model">{options(MODELS, 'flux2-klein-4b', MODELS)}</select>
<label>on<input type="number" name="rotate" min="1" max="20" value="4"></label><span class="muted">test characters</span>
<button{disabled}>Try out</button></form>
<a class="chip" href="{link('/generate', lora=loras[0][0])}">Use in Generate</a>"""

    return f"""<article class="card run">
<header><h2>{escape(run['name'])}</h2><span class="muted">{escape(task)} · {escape(model)} · {settings.get('size', '?')}px · {escape(sources)}</span></header>
<p><strong>step {run['step']:,} of {run['steps']:,}</strong> · check score {val_now}{escape(left)}</p>
<div class="bar"><span style="width:{progress}%"></span></div>
{chart(run)}<div class="actions">{actions}</div></article>"""


def training_page(data: Path, job: dict | None, log: str, form: dict, message: str = "") -> str:
    running = bool(job and job["status"] == "running")
    runs = read_runs(data)
    cards = "".join(run_card(data, run, running) for run in runs) or '<p class="muted">No training runs yet.</p>'

    export_names = exports(data)
    export = form.get("export", export_names[0] if export_names else "")
    sources = export_sources(data, export) if export else []
    licences = read_json(data / "exports" / export / "export.json").get("sources", {}) if export else {}
    chosen = form.get("sources_list") or sources
    source_boxes = "".join(
        f'<label class="check"><input type="checkbox" name="sources" value="{escape(name)}"{" checked" if name in chosen else ""}>'
        f'{escape(name)} <span class="muted">{escape(licences.get(name, {}).get("license", ""))}</span></label>'
        for name in sources
    )
    disabled = " disabled" if running else ""

    new_run = f"""<form method="post" action="/training/start" class="panel">
<label>Name<input name="name" required pattern="[A-Za-z0-9_-]{{1,40}}" value="{escape(form.get('name', ''))}" placeholder="rotate-v3"></label>
<label>Task<select name="task">{options(TASKS, form.get('task', 'rotate'), TASKS)}</select></label>
<label>Export<select name="export">{options(export_names, export)}</select></label>
<label>Model<select name="model">{options(MODELS, form.get('model', 'flux2-klein-base-4b'), MODELS)}</select></label>
<label>Size<select name="size">{options(SIZES, form.get('size', '256'), {s: f'{s} px' for s in SIZES})}</select></label>
<label>Steps<input type="number" name="steps" min="1" max="50000" value="{escape(form.get('steps', '2000'))}"></label>
<fieldset class="wide"><legend>Sources</legend>{source_boxes or '<span class="muted">No export yet: run <code>uv run pixel export</code>.</span>'}</fieldset>
<button{disabled}>Start training</button>
<p class="muted wide">About 28 s per step at 256 px and 77 s at 512 px on an M1 Max. A source with an NC licence makes the result non-commercial. Create trains on characters with a caption (lpc-4view) or an AI label in data/labels (pac).</p>
</form>"""

    return f"""<h1>Training</h1>
{message_block(message)}{job_panel(job, log, "/training")}
<section class="cards runs">{cards}</section>
<h2>New run</h2>{new_run}{POLL}"""
