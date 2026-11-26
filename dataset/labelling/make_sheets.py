"""Put export characters on numbered sheets of 16, for an AI labeller to look at.

    uv run python labelling/make_sheets.py <out folder> --count 1000 --source lpc-4view

Writes <out>/sheets/sheet-NNN.png and <out>/key.json (number -> character and its true caption, if any).
"""

import argparse
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CELL, GRID, LABEL = 192, 4, 22


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--export", type=Path, default=Path("data/exports/rotation-v1-data"))
    parser.add_argument("--source", default="lpc-4view")
    parser.add_argument("--split", default="train", help="train, val, test or all")
    parser.add_argument("--count", type=int, default=1000, help="0 for every character, in export order")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    rows = [json.loads(line) for line in (args.export / "characters.jsonl").read_text().splitlines()]
    rows = [row for row in rows if row["source"] == args.source and args.split in ("all", row["split"])]
    pick = rows if args.count == 0 else random.Random(args.seed).sample(rows, min(args.count, len(rows)))

    (args.out / "sheets").mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=18)
    key = []
    per_sheet = GRID * GRID
    for start in range(0, len(pick), per_sheet):
        name = f"sheet-{start // per_sheet + 1:03d}.png"
        sheet = Image.new("RGB", (CELL * GRID, (CELL + LABEL) * GRID), "white")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(pick[start:start + per_sheet]):
            number = start + index + 1
            x, y = (index % GRID) * CELL, (index // GRID) * (CELL + LABEL)
            sprite = Image.open(args.export / row["views"]["front"]).convert("RGBA").resize((CELL, CELL), Image.NEAREST)
            sheet.paste(sprite, (x, y + LABEL), sprite)
            draw.rectangle([x, y, x + CELL - 1, y + CELL + LABEL - 1], outline=(180, 180, 180))
            draw.text((x + 6, y + 2), f"#{number}", fill="black", font=font)
            key.append({"n": number, "sheet": name, "character": row["character"], "truth": row.get("caption")})
        sheet.save(args.out / "sheets" / name)

    (args.out / "key.json").write_text(json.dumps(key, indent=1))
    print(f"{len(key)} characters on {len(key) // per_sheet + bool(len(key) % per_sheet)} sheets in {args.out}")


if __name__ == "__main__":
    main()
