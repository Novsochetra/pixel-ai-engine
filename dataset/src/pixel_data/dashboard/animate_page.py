"""The Animate page: give a generated character, or a PNG you upload, to `pixel-train animate`.

Uploads are checked with Pillow and saved again as a clean PNG under data/uploads/, so the job
reads a file the dashboard made. The results of every run are read back from data/animated/.
"""

import io
import json
import re
from datetime import datetime
from html import escape
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from pixel_data.dashboard.browse_pages import link, readable_time
from pixel_data.dashboard.studio import POLL, Invalid, job_panel, message_block, one_of, options, read_generated, read_json

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
GALLERY = 30
SPRITE = re.compile(r"^s(\d+)-(front|left|back|right)\.png$")
# generated/<folder>/s<seed>, or generated/<folder> for its first character (the Generate page links so).
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


# Drawing the page


def source_options(data: Path, chosen: str) -> tuple[str, str]:
    """The <option>s for the source picker, and the first sprite of the chosen one to show."""
    made = []
    for item in characters(data):
        for index, (seed, views) in enumerate(item["sprites"].items()):
            value = f"generated/{item['folder']}/s{seed}"
            # A link to the folder alone picks its first character.
            picked = value == chosen or (index == 0 and chosen == f"generated/{item['folder']}")
            made.append(
                f'<option value="{escape(value)}" data-subject="{escape(item["prompt"])}" data-views="{escape(json.dumps(views))}"'
                f'{" selected" if picked else ""}>{escape(item["prompt"][:70])} · {escape(item["folder"])} · s{seed}</option>'
            )
    old = [f'<option value="uploads/{escape(name)}"{" selected" if f"uploads/{name}" == chosen else ""}>{escape(name)}</option>'
           for name in uploads(data)]

    html = f'<option value="upload"{" selected" if chosen == "upload" else ""}>Upload a new PNG…</option>'
    if made:
        html += f'<optgroup label="Generated characters">{"".join(made)}</optgroup>'
    if old:
        html += f'<optgroup label="Uploaded before">{"".join(old)}</optgroup>'

    return html, chosen


def checks(name: str, values: dict | tuple, chosen: list[str]) -> str:
    labels = values if isinstance(values, dict) else {value: value for value in values}

    return "".join(
        f'<label class="check"><input type="checkbox" name="{name}" value="{escape(value)}"{" checked" if value in chosen else ""}>{escape(label)}</label>'
        for value, label in labels.items()
    )


def gallery(data: Path) -> str:
    items = []
    for run in read_animated(data)[:GALLERY]:
        folder = run["folder"]
        clips = "".join(
            f'<figure class="clip"><a href="{link(f"/animated/{folder}/{clip["id"]}.gif")}">'
            f'<img class="gif" src="{link(f"/animated/{folder}/{clip["id"]}.gif")}" alt="{escape(clip["id"])}" loading="lazy"></a>'
            f'<figcaption>{escape(clip["id"])} · {clip.get("used", "?")} frames</figcaption>'
            f'<span><a href="{link(f"/animated/{folder}/{clip["id"]}-raw.gif")}">raw video</a> · '
            f'<a href="{link(f"/animated/{folder}/{clip["id"]}-sheet.png")}">sheet</a></span></figure>'
            for clip in run["clips"]
        ) or '<p class="muted">No clips yet. A running job adds each clip when it is done.</p>'
        source = Path(run.get("source", folder)).name
        details = [f"{run.get('size', '?')}px", f"{run.get('frames', '?')} frames"]
        if run.get("same_end") is False:
            details.append("open end")
        when = escape(readable_time(run["created_at"])) if run.get("created_at") else ""
        subject = f'<p class="muted">{escape(run["subject"])}</p>' if run.get("subject") else ""
        items.append(f'<article class="row"><header><strong>{escape(source)}</strong>'
                     f'<span class="muted">{when} · {escape(" · ".join(details))} · {escape(folder)}</span></header>'
                     f'{subject}<div class="clips">{clips}</div></article>')

    return "".join(items) or '<p class="muted">Nothing animated yet.</p>'


SCRIPT = """<script>
(function () {
  const form = document.getElementById('animate-form');
  if (!form) return;
  const source = form.elements.source, subject = form.elements.subject, actions = form.elements.actions;
  const file = form.elements.image, preview = document.getElementById('animate-preview');
  const views = form.querySelectorAll('input[name=views]');
  const estimate = document.getElementById('animate-estimate');
  const minutes = MINUTES;
  let typed = subject.value !== '';
  subject.addEventListener('input', () => { typed = subject.value !== ''; });

  function chosen() { return source.options[source.selectedIndex]; }
  function generated() { return source.value.startsWith('generated/'); }
  function has() { return JSON.parse(chosen().dataset.views || '[]'); }

  function show() {
    form.querySelectorAll('[data-for=generated]').forEach((part) => { part.hidden = !generated(); });
    form.querySelectorAll('[data-for=new]').forEach((part) => { part.hidden = source.value !== 'upload'; });
    file.required = source.value === 'upload';
    if (generated()) {
      const ok = has();
      views.forEach((box) => { box.disabled = !ok.includes(box.value); if (box.disabled) box.checked = false; });
      if (![...views].some((box) => box.checked)) views.forEach((box) => { if (!box.disabled && box.value !== 'back') box.checked = true; });
      if (!typed) subject.value = chosen().dataset.subject || '';
    } else if (!typed) {
      subject.value = '';  // the words of a generated character do not fit an uploaded picture
    }
    picture();
    count();
  }

  function picture() {
    let url = '';
    if (generated()) {
      const view = [...views].find((box) => box.checked)?.value || has()[0];
      if (view) url = '/' + source.value + '-' + view + '.png';
    } else if (source.value === 'upload') {
      if (file.files[0]) url = URL.createObjectURL(file.files[0]);
    } else {
      url = '/' + source.value;
    }
    preview.hidden = !url;
    if (url) preview.src = url;
  }

  function count() {
    const many = generated() ? [...views].filter((box) => box.checked).length : 1;
    const lines = actions.value.split('\\n').map((line) => line.trim().replace(/\\s+/g, ' ').toLowerCase()).filter(Boolean);
    const clips = many * new Set(lines).size;
    const each = minutes[form.elements.size.value + '-' + form.elements.frames.value] || 11;
    estimate.textContent = clips
      ? clips + ' clip' + (clips > 1 ? 's' : '') + ', about ' + clips * each + ' min, plus a few minutes to load the models.'
      : 'Say at least one action.';
  }

  form.addEventListener('change', (event) => { if (event.target === source) show(); else { picture(); count(); } });
  file.addEventListener('change', picture);
  actions.addEventListener('input', count);
  show();
})();
</script>"""


def animate_page(data: Path, job: dict | None, log: str, form: dict, message: str = "") -> str:
    known = characters(data)
    first = f"generated/{known[0]['folder']}" if known else "upload"
    source_html, chosen = source_options(data, form.get("source", first))
    running = bool(job and job["status"] == "running")
    views = form.get("views_list") or ["front", "right"]
    actions = form.get("actions", DEFAULT_ACTIONS)
    minutes = json.dumps({f"{size}-{frames}": value for (size, frames), value in MINUTES.items()})

    return f"""<h1>Animate</h1>
{message_block(message)}{job_panel(job, log, "/animate")}
<form method="post" action="/animate" enctype="multipart/form-data" class="panel" id="animate-form">
<label class="wide">Character<select name="source">{source_html}</select></label>
<label class="wide" data-for="new">PNG to animate<input type="file" name="image" accept="image/png,image/*"></label>
<img id="animate-preview" class="preview wide" alt="The sprite to animate" hidden>
<label class="wide">What the sprite shows<textarea name="subject" rows="2" maxlength="300" placeholder="a knight in grey armour with a blue cape, empty hands">{escape(form.get("subject", ""))}</textarea></label>
<p class="muted wide">Name only what the picture shows. A sword in the words gives the character a sword, even when the sprite has none. For your own PNG, you can also say which way it faces.</p>
<fieldset class="wide" data-for="generated"><legend>Views</legend>{checks("views", VIEWS, views)}</fieldset>
<label class="wide">Actions, one a line<textarea name="actions" rows="3" placeholder="idle&#10;walk&#10;flaps its wings and hovers">{escape(actions)}</textarea></label>
<p class="muted wide">Each line is one clip. idle, walk and attack have ready words: idle keeps the pose (a flying dragon keeps flying), walk is for characters with legs. Any other line is used as you write it. Every clip ends on the sprite, so it loops.</p>
<label>Video size<select name="size">{options(SIZES, form.get("size", "384"), SIZES)}</select></label>
<label>Length<select name="frames">{options(FRAMES, form.get("frames", "33"), FRAMES)}</select></label>
<button{" disabled" if running else ""}>Animate</button>
<p class="muted wide" id="animate-estimate">About 11 min a clip at 384 px and 33 frames on an M1 Max.</p>
</form>
<h2>Animated so far</h2><section class="rows wide">{gallery(data)}</section>{POLL}{SCRIPT.replace("MINUTES", minutes)}"""
