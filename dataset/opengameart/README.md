# OpenGameArt sprites for create training

The sprites come from many packs, cut by `cut.py`, so many are not characters (items, trees, effects)
or do not face the viewer. The labeller writes `skip` for those; training leaves them out.

Cut the sprites, make the export and the sheets, run the labellers as for pac (see
`../labelling/README.md`), then collect the labels:

```bash
uv run --with numpy --with scipy --with zstandard python opengameart/cut.py data/opengameart
uv run python opengameart/export.py data/opengameart data/exports/opengameart-v1-data
uv run python labelling/make_sheets.py data/labels/opengameart --export data/exports/opengameart-v1-data --source opengameart-2d --split all --count 0
python3 labelling/collect.py data/labels/opengameart
```

Each Haiku 5.5 agent (medium effort) got this prompt, with its own sheet list:

```text
You label pixel art sprites for an image-model training set.

Folder: <the folder from make_sheets.py>

Your sheets (in sheets/): sheet-001.png ... sheet-013.png

Each sheet is a 4x4 grid of sprites cut from many free game art packs. Each cell is numbered "#N" at the top left.

For each sheet, one at a time:
1. Read the sheet image with the Read tool.
2. For each cell, first decide: is it ONE whole character or creature (a person, monster, animal, robot), standing or floating, facing the viewer (front view, or turned only a little)?
   - Write exactly "skip" if it is an item, weapon, tile, tree, plant, building, effect, text, a symbol, only a head or part of a body, more than one character, a vehicle, seen from the side or the back, or lying down.
   - Otherwise write one short label in simple English, 6-20 words: what it is, then its main colours, clothes or body parts, and what it holds. Rules:
     - Do NOT say man, woman, boy, girl, male or female. Say "a character", "a person", or what the creature is.
     - Name only what you see. Do not guess a story.
   Examples:
   "a knight in gray armour with a red plume, holding a sword and a round shield"
   "a green slime monster with big black eyes"
   "a small robot with a blue body, round head and antenna"
   "a person with brown hair in a green tunic and brown boots"
   Do not mention pixel art, the background or the view.
3. Write the labels for that sheet to out/<sheet name>.jsonl, one JSON object per line: {"n": 1, "label": "..."}. "n" is the number in the cell. One line per cell, "skip" included.

Write each sheet's file before you read the next sheet. Do not read any other files. When all your sheets are done, reply with only: the sheet files you wrote, how many labels, and how many were "skip".
```

## Result (2026-11-24)

`cut.py` kept 5,418 sprites from 840 pages (78,789 pictures; frames of one character and pages over
40 sprites are left out). Haiku kept 1,386 as characters (1,308 train, 78 val) and wrote `skip`
for 4,032. By eye, about 1 kept sprite in 16 is not a character (a helmet, a button). 27 agents,
about 7 minutes.
