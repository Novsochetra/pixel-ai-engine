"""The training loop, without the model: what to train on, when to save, how to pick up again.

Two tasks train the same way. "rotate": the front view in, another view out. "create": the
character's caption in, its front view out.

The model side (FLUX.2 Klein with a LoRA) is in lora.py. The loop only needs something with the
Backend methods, so the tests run it with a stand-in.
"""

import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

CHECKPOINTS = "checkpoints"
FINAL = "final"


# A labeller writes this for a picture that is not one character seen from the front.
SKIP = "skip"
# The pose and view words in the create template. Every training sprite stands and faces the
# viewer, so training always uses these.
POSE = "standing"
FRONT = "front view facing the viewer"
# The view words for a character drawn from the side, flying or running to the right.
SIDE = "side view, facing right, seen from the side"
CAPTION_PREFIX = "lpc-style pixel art character, "


@dataclass(frozen=True)
class Pair:
    character: str
    view: str
    front: Path | None  # None for "create": there is no picture in, only the caption
    target: Path
    caption: str | None = None


@dataclass(frozen=True)
class Settings:
    model: str
    export: str
    size: int
    steps: int
    rank: int
    learning_rate: float
    accumulate: int
    every: int
    val_count: int
    sources: tuple[str, ...]
    seed: int
    task: str = "rotate"
    more_exports: tuple[str, ...] = ()  # create only: more exports whose captioned characters join in
    more_repeat: int = 1
    repeat: tuple[tuple[str, float], ...] = ()  # (source, times): 5 shows it 5 times as often, 0.5 half of it


class Backend(Protocol):
    def train_step(self, pairs: list[Pair]) -> float:
        """Learn from these pairs (one optimiser step) and return the mean loss."""

    def val_loss(self, pairs: list[Pair]) -> float:
        """The loss on these pairs, with the same noise every time, so checkpoints compare."""

    def save(self, folder: Path) -> None:
        """Write the LoRA and the optimiser state to the folder."""

    def load(self, folder: Path) -> None:
        """Read back what save wrote."""


def read_pairs(export: Path, split: str, views: list[str], sources: tuple[str, ...] = ()) -> list[Pair]:
    """One pair per character and view: its front view in, that view out."""
    pairs = []
    for line in (export / "characters.jsonl").read_text().splitlines():
        entry = json.loads(line)
        if entry["split"] != split or (sources and entry["source"] not in sources):
            continue

        for view in views:
            if view in entry["views"]:
                pairs.append(Pair(entry["character"], view, export / entry["views"]["front"], export / entry["views"][view]))

    return pairs


def caption_text(caption: str, template: str) -> str:
    """An export caption in the words `generate` uses, so the LoRA learns what it will be asked.

    "lpc-style pixel art character, with male human body, ..." becomes the create template around
    "a character with male human body, ...".
    """
    subject = caption.removeprefix(CAPTION_PREFIX).strip().rstrip(".")

    return template.format(subject=f"a character {subject}" if subject.startswith("with ") else subject, pose=POSE, view=FRONT)


def read_labels(folder: Path) -> dict[str, str]:
    """AI labels from dataset/labelling: every <folder>/<name>/labels.jsonl, character -> label."""
    labels = {}
    for path in sorted(folder.glob("*/labels.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                labels[row["character"]] = row["label"]

    return labels


def read_captioned(export: Path, split: str, template: str, sources: tuple[str, ...] = (),
                   labels: dict[str, str] | None = None) -> list[Pair]:
    """One pair per character with a caption: its caption in, its front view out.

    The export's own caption wins (lpc-4view's comes from its art layers); a character without one
    takes its AI label, if it has one.
    """
    labels = labels or {}
    pairs = []
    for line in (export / "characters.jsonl").read_text().splitlines():
        entry = json.loads(line)
        if entry["split"] != split or (sources and entry["source"] not in sources):
            continue

        caption = entry.get("caption") or labels.get(entry["character"])
        if caption and caption != SKIP and "front" in entry["views"]:
            pairs.append(Pair(entry["character"], "front", None, export / entry["views"]["front"],
                              caption_text(caption, template)))

    return pairs


def source_of(pair: Pair) -> str:
    return pair.character.split("/", 1)[0]


def repeated(pairs: list[Pair], times: dict[str, float], seed: int) -> list[Pair]:
    """Show some sources more or less often.

    A small source would hardly be seen next to a big one. 5 puts each of its pairs in 5 times;
    0.5 keeps a fixed half of them (the same half every run, so a resumed run sees the same pairs).
    """
    kept = []
    for source in dict.fromkeys(source_of(pair) for pair in pairs):
        group = [pair for pair in pairs if source_of(pair) == source]
        share = times.get(source, 1)
        whole = int(share)
        kept += group * whole
        kept += random.Random(f"{seed}-{source}").sample(group, round((share - whole) * len(group)))

    return kept


def val_sample(pairs: list[Pair], count: int, seed: int) -> list[Pair]:
    return random.Random(seed).sample(pairs, min(count, len(pairs)))


def checkpoint_name(step: int) -> str:
    return f"step-{step:06d}"


def latest_checkpoint(run: Path) -> tuple[int, Path] | None:
    folders = sorted((run / CHECKPOINTS).glob("step-*")) if (run / CHECKPOINTS).is_dir() else []
    done = [folder for folder in folders if (folder / "state.json").is_file()]
    if not done:
        return None

    return json.loads((done[-1] / "state.json").read_text())["step"], done[-1]


def lora_folder(path: Path) -> Path:
    """A run folder, or one of its checkpoints, to the folder that holds the LoRA to load."""
    if (path / FINAL).is_dir():
        return path / FINAL

    found = latest_checkpoint(path)

    return found[1] if found else path


def run_settings(path: Path) -> dict:
    """The settings of the run a LoRA folder belongs to, so a try-out can match its size."""
    for folder in (path, *path.parents):
        if (folder / "run.json").is_file():
            return json.loads((folder / "run.json").read_text())["settings"]

    return {}


class Order:
    """Which pairs each step learns from: every pair once in a shuffled order, then again in a new one.

    So 500 steps a day go through all the data before any picture comes back. The order depends
    only on the seed and the pairs, so a resumed run sees what an unbroken one would have.
    """

    def __init__(self, pairs: list[Pair], seed: int, batch: int):
        self.pairs, self.seed, self.batch = pairs, seed, min(batch, len(pairs))
        self.orders: dict[int, list[int]] = {}

    def order(self, number: int) -> list[int]:
        if number not in self.orders:
            self.orders = {key: value for key, value in self.orders.items() if key >= number - 1}
            order = list(range(len(self.pairs)))
            random.Random(self.seed * 1_000_003 + number).shuffle(order)
            self.orders[number] = order

        return self.orders[number]

    def picks(self, step: int) -> list[Pair]:
        positions = range((step - 1) * self.batch, step * self.batch)

        return [self.pairs[self.order(at // len(self.pairs))[at % len(self.pairs)]] for at in positions]

    def passes(self, step: int) -> float:
        """How many times over the whole data the run has gone after this step."""
        return step * self.batch / len(self.pairs)


def log(run: Path, row: dict) -> None:
    with (run / "log.jsonl").open("a") as file:
        file.write(json.dumps(row) + "\n")


def save_checkpoint(run: Path, backend: Backend, step: int, val: float | None) -> Path:
    # Written to a temporary name first: a crash halfway leaves no checkpoint that looks complete.
    folder = run / CHECKPOINTS / checkpoint_name(step)
    partial = folder.with_name(folder.name + ".partial")
    partial.mkdir(parents=True, exist_ok=True)
    backend.save(partial)
    (partial / "state.json").write_text(json.dumps({"step": step, "val_loss": val}))
    partial.rename(folder)

    return folder


def train(run: Path, settings: Settings, train_pairs: list[Pair], val_pairs: list[Pair], backend: Backend,
          resume: bool = False, say=print) -> dict:
    run.mkdir(parents=True, exist_ok=True)
    start = 0

    found = latest_checkpoint(run) if resume else None
    if found:
        start, folder = found
        backend.load(folder)
        say(f"Picked up from {folder.name}")
    elif (run / "log.jsonl").exists():
        raise FileExistsError(f"{run} already has a run in it. Use --resume to go on with it, or another --name.")

    (run / "run.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "settings": asdict(settings),
        "train_pairs": len(train_pairs),
        "val_pairs": [asdict(pair) | {"front": pair.front and str(pair.front), "target": str(pair.target)}
                      for pair in val_pairs],
    }, indent=2))

    order = Order(train_pairs, settings.seed, settings.accumulate)
    started = time.monotonic()
    val = None

    for step in range(start + 1, settings.steps + 1):
        loss = backend.train_step(order.picks(step))
        row = {"step": step, "loss": round(loss, 5), "passes": round(order.passes(step), 4)}

        if step % settings.every == 0 or step == settings.steps:
            val = backend.val_loss(val_pairs)
            row["val_loss"] = round(val, 5)
            save_checkpoint(run, backend, step, val)

        seconds = (time.monotonic() - started) / (step - start)
        row["seconds_per_step"] = round(seconds, 2)
        log(run, row)

        left = (settings.steps - step) * seconds / 60
        extra = f", val {row['val_loss']:.4f}, saved" if "val_loss" in row else ""
        say(f"step {step}/{settings.steps}: loss {loss:.4f}{extra}, {row['passes']:.1%} of the data"
            f" ({seconds:.1f}s per step, ~{left:.0f} min left)")

    final = run / FINAL
    final.mkdir(exist_ok=True)
    backend.save(final)

    return {"steps": settings.steps, "val_loss": val, "final": str(final)}
