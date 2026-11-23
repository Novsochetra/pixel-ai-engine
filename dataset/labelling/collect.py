"""Collect the AI labels of a labelling folder into one file, one line per character.

    python3 labelling/collect.py data/labels/pac

Reads <folder>/key.json (from make_sheets.py) and <folder>/out/sheet-NNN.jsonl (from the labeller),
and writes <folder>/labels.jsonl: {"character": ..., "label": ...}. Prints which sheets are missing
labels, so they can be labelled again.
"""

import json
import sys
from pathlib import Path

folder = Path(sys.argv[1])
key = json.loads((folder / "key.json").read_text())
numbers = {}
for item in key:
    numbers.setdefault(item["sheet"].removesuffix(".png"), []).append(item["n"])

found = {}
for path in sorted((folder / "out").glob("sheet-*.jsonl")):
    cells = numbers.get(path.stem, [])
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
            label = " ".join(str(row["label"]).split())
            n = int(row["n"])
        except (ValueError, KeyError, TypeError):
            continue
        # A labeller sometimes counts 1-16 on each sheet instead of using the cell numbers.
        if n not in cells and 1 <= n <= len(cells):
            n = cells[n - 1]
        if label and n in cells:
            found[n] = label

missing = [item for item in key if item["n"] not in found]
with (folder / "labels.jsonl").open("w") as file:
    for item in key:
        if item["n"] in found:
            file.write(json.dumps({"character": item["character"], "label": found[item["n"]]}) + "\n")

print(f"{len(key) - len(missing)} of {len(key)} characters labelled -> {folder / 'labels.jsonl'}")
if missing:
    sheets = sorted({item["sheet"] for item in missing})
    print(f"{len(missing)} without a label, on {len(sheets)} sheets: {' '.join(sheets[:40])}{' ...' if len(sheets) > 40 else ''}")
