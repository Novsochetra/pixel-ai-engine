import json
from pathlib import Path

from pixel_data.dashboard.invalid import Invalid

MOST_TIMES = 20


def read_export(data: Path, export: str) -> dict:
    try:
        return json.loads((data / "exports" / export / "export.json").read_text())
    except (OSError, ValueError):
        return {}


# Older exports keep no counts, so None means every source they list may have characters.
def train_counts(data: Path, export: str) -> dict[str, int] | None:
    characters = read_export(data, export).get("characters")
    counts = characters.get("train") if isinstance(characters, dict) else None

    return counts if isinstance(counts, dict) else None


# An export lists the licence of every source it read, even one that gave it nothing to train on.
def trainable_sources(data: Path, export: str) -> list[str]:
    sources = read_export(data, export).get("sources", {})
    counts = train_counts(data, export)

    return sorted(source for source in sources if counts is None or counts.get(source, 0) > 0)


def more_exports(form: dict, task: str, export: str, known: list[str]) -> list[str]:
    chosen = form.get("more_exports", [])
    if chosen and task != "create":
        raise Invalid("Only a create run takes more exports.")
    if any(name not in known or name == export for name in chosen):
        raise Invalid("Pick more exports from the list.")

    return list(dict.fromkeys(chosen))


def repeat_args(form: dict, sources: list[str]) -> list[str]:
    args = []
    for source, times in form.get("repeat", {}).items():
        if source not in sources:
            raise Invalid(f"{source} is not in this run, so it cannot repeat.")
        if isinstance(times, bool) or not isinstance(times, int | float) or not 0 < times <= MOST_TIMES:
            raise Invalid(f"Repeat a source more than 0 and at most {MOST_TIMES} times.")
        if times != 1:
            args.append(f"{source}={times:g}")

    return ["--repeat", *args] if args else []
