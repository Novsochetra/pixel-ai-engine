import json
from collections import Counter, defaultdict
from pathlib import Path

from pixel_data.analyze.store import split_flags
from pixel_data.export.fix import fixed
from pixel_data.export.select import REQUIRED_VIEWS
from pixel_data.images import load_image

FORMAT_NOTE = """# {name}

Made by `pixel export` on {created_at}. Do not edit by hand: run the export again.

- `characters.jsonl`: one line per character: `character`, `source`, `split` (train, val or test),
  `license`, `caption`, and `views`, the path of each view's PNG under this folder.
- `images/<split>/<source>/<character>/<view>.png`: the pictures, fixed (no half-transparent pixels)
  and at their true pixel size.
- `export.json`: what went in, what was left out and why, and the leak checks.

Characters that look almost the same are always in the same split, so the test set only holds
characters the model never saw.
"""


def local_name(character: str, source: str) -> str:
    return character.removeprefix(f"{source}/").replace("/", "-")


def write_character(folder: Path, raw: Path, character: dict, split: str) -> dict:
    target = Path("images") / split / character["source"] / local_name(character["character"], character["source"])
    (folder / target).mkdir(parents=True, exist_ok=True)

    views = {}
    for view in REQUIRED_VIEWS:
        row = character["views"][view]
        image = fixed(load_image(raw, row), split_flags(row["flags"]), row["scale"])
        image.save(folder / target / f"{view}.png")
        views[view] = str(target / f"{view}.png")

    return {
        "character": character["character"],
        "source": character["source"],
        "split": split,
        "license": character["license"],
        "caption": character["caption"],
        "views": views,
    }


def leak_checks(characters: list[dict], splits: dict[str, str]) -> dict:
    group_splits, picture_splits = defaultdict(set), defaultdict(set)

    for character in characters:
        split = splits[character["character"]]
        group_splits[character["group"]].add(split)

        for view in character["views"].values():
            picture_splits[view["pixel_hash"]].add(split)

    return {
        "groups_in_two_splits": sum(1 for found in group_splits.values() if len(found) > 1),
        "pictures_in_two_splits": sum(1 for found in picture_splits.values() if len(found) > 1),
    }


def counts_by_split(entries: list[dict]) -> dict:
    counts = defaultdict(Counter)
    for entry in entries:
        counts[entry["split"]][entry["source"]] += 1

    return {split: dict(sources) for split, sources in counts.items()}


def write_files(folder: Path, entries: list[dict], summary: dict) -> None:
    with (folder / "characters.jsonl").open("w") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")

    (folder / "export.json").write_text(json.dumps(summary, indent=2))
    (folder / "README.md").write_text(FORMAT_NOTE.format(name=summary["name"], created_at=summary["created_at"]))
