import json
import random
from pathlib import Path

from pixel_data.export.split import SPLITS

SAMPLES_PER_SPLIT = 6


def read_exports(folder: Path) -> list[dict]:
    summaries = []
    for summary in sorted(folder.glob("*/export.json")):
        summaries.append(json.loads(summary.read_text()))

    return sorted(summaries, key=lambda summary: summary["created_at"], reverse=True)


def samples(folder: Path, name: str) -> dict[str, list[dict]]:
    by_split = {split: [] for split in SPLITS}

    with (folder / name / "characters.jsonl").open() as handle:
        for line in handle:
            entry = json.loads(line)
            by_split[entry["split"]].append(entry)

    # The same picks on every visit, so a reload does not reshuffle what you were looking at.
    pick = random.Random(name)

    return {split: pick.sample(entries, min(SAMPLES_PER_SPLIT, len(entries))) for split, entries in by_split.items()}
