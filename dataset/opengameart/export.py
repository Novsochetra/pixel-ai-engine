"""Turn the cut OpenGameArt sprites into an export that create training can read.

    uv run python opengameart/export.py data/opengameart data/exports/opengameart-v1-data

Every sprite becomes a character with only a front view, and no caption: the AI labels in
data/labels/opengameart give it one (a "skip" label leaves it out). The split goes by page, so the
sprites of one pack are never in two splits: about 1 page in 20 is "val".
"""

import argparse
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SOURCE, LICENSE = "opengameart-2d", "CC0"


def split_of(page: str) -> str:
    return "val" if int(hashlib.sha1(page.encode()).hexdigest(), 16) % 20 == 0 else "train"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cut", type=Path, help="the folder cut.py wrote")
    parser.add_argument("out", type=Path)
    args = parser.parse_args()

    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)
    counts = Counter()
    with (args.out / "characters.jsonl").open("w") as file:
        for line in (args.cut / "sprites.jsonl").read_text().splitlines():
            sprite = json.loads(line)
            split = split_of(sprite["page"])
            front = Path("images") / split / SOURCE / str(sprite["n"]) / "front.png"
            (args.out / front).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(args.cut / "sprites" / f"{sprite['n']}.png", args.out / front)
            file.write(json.dumps({"character": f"{SOURCE}/{sprite['n']}", "source": SOURCE, "split": split,
                                   "license": LICENSE, "caption": None, "views": {"front": str(front)},
                                   "page": sprite["page"], "author": sprite["author"]}) + "\n")
            counts[split] += 1

    revision = json.loads(Path("data/raw/opengameart-2d/_source.json").read_text())["revision"]
    (args.out / "export.json").write_text(json.dumps({
        "name": args.out.name, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": {SOURCE: {"license": LICENSE, "use": "train", "revision": revision}},
        "characters": {split: {SOURCE: count} for split, count in counts.items()},
    }, indent=1))
    print(f"{sum(counts.values())} sprites ({dict(counts)}) -> {args.out}")


if __name__ == "__main__":
    main()
