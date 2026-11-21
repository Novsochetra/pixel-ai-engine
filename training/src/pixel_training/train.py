"""The training loop, without the model: what to train on, when to save, how to pick up again.

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


@dataclass(frozen=True)
class Pair:
    character: str
    view: str
    front: Path
    target: Path


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
        "val_pairs": [asdict(pair) | {"front": str(pair.front), "target": str(pair.target)} for pair in val_pairs],
    }, indent=2))

    # The order of the pairs depends only on the seed and the step, so a resumed run sees what an
    # unbroken one would have.
    batch = settings.accumulate
    started = time.monotonic()
    val = None

    for step in range(start + 1, settings.steps + 1):
        picks = random.Random(settings.seed * 1_000_003 + step).sample(train_pairs, min(batch, len(train_pairs)))
        loss = backend.train_step(picks)
        row = {"step": step, "loss": round(loss, 5)}

        if step % settings.every == 0 or step == settings.steps:
            val = backend.val_loss(val_pairs)
            row["val_loss"] = round(val, 5)
            save_checkpoint(run, backend, step, val)

        seconds = (time.monotonic() - started) / (step - start)
        row["seconds_per_step"] = round(seconds, 2)
        log(run, row)

        left = (settings.steps - step) * seconds / 60
        extra = f", val {row['val_loss']:.4f}, saved" if "val_loss" in row else ""
        say(f"step {step}/{settings.steps}: loss {loss:.4f}{extra} ({seconds:.1f}s per step, ~{left:.0f} min left)")

    final = run / FINAL
    final.mkdir(exist_ok=True)
    backend.save(final)

    return {"steps": settings.steps, "val_loss": val, "final": str(final)}
