import json
from pathlib import Path


def read_runs(folder: Path) -> list[dict]:
    runs = [json.loads(path.read_text()) for path in folder.glob("*/results.json")] if folder.exists() else []

    return sorted(runs, key=lambda run: run["created_at"], reverse=True)


def finished_models(run: dict) -> list[str]:
    return [name for name, result in run["models"].items() if "create" in result]
