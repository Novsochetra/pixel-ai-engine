import json
from pathlib import Path

SETTINGS = {"model": "flux2-klein-base-4b", "export": "rotation-v1", "size": 256, "steps": 20, "rank": 16,
            "learning_rate": 0.0001, "accumulate": 4, "every": 10, "val_count": 16, "sources": ["pac"], "seed": 0}
LICENCES = {"pac": {"license": "CC-BY-NC-4.0", "use": "train"},
            "lpc-4view": {"license": "CC-BY-SA-3.0", "use": "train"}}


def write_run(data: Path, name: str, info: dict, rows: list[dict]) -> Path:
    run = data / "runs" / name
    run.mkdir(parents=True)
    (run / "run.json").write_text(json.dumps(info))
    (run / "log.jsonl").write_text("\n".join(json.dumps(row) for row in rows))

    return run


def save_checkpoint(run: Path, step: int) -> None:
    folder = run / "checkpoints" / f"step-{step:06d}"
    folder.mkdir(parents=True)
    (folder / "state.json").write_text(json.dumps({"step": step}))


def rotate_run(data: Path) -> None:
    rows = [{"step": step, "loss": 0.2 - step / 200, "seconds_per_step": 27.0} for step in range(1, 21)]
    rows[9]["val_loss"], rows[19]["val_loss"] = 0.15, 0.12
    run = write_run(data, "rotate-v2", {"created_at": "2026-11-20T10:00:00+00:00", "settings": SETTINGS}, rows)
    save_checkpoint(run, 10)
    (run / "final").mkdir()
    (run / "final" / "pytorch_lora_weights.safetensors").write_text("lora")


def create_run(data: Path) -> None:
    settings = {**SETTINGS, "task": "create", "sources": [], "more_exports": ["opengameart-v1"],
                "repeat": [["pac", 5.0]]}
    rows = [{"step": step, "loss": 0.1, "passes": step / 100, "seconds_per_step": 28.0} for step in range(1, 11)]
    run = write_run(data, "pixie-draw-v1", {"created_at": "2026-11-25T10:00:00+00:00", "settings": settings}, rows)
    save_checkpoint(run, 10)


def write_export(data: Path) -> None:
    export = data / "exports" / "rotation-v1"
    export.mkdir(parents=True)
    (export / "characters.jsonl").write_text("")
    (export / "export.json").write_text(json.dumps({"sources": LICENCES}))


# A small data folder: a rotate run with a checkpoint and a final, a newer create run, one export.
def training_data(data: Path) -> Path:
    rotate_run(data)
    create_run(data)
    write_export(data)

    return data
