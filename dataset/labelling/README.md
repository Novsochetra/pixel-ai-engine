# Labelling with an AI

A create LoRA learns from labels (captions). lpc-4view has exact labels made from its art layers;
pac and the other new sources have none. These tools test how well an AI labeller does, on LPC
characters, where the true labels are known.

1. `uv run python labelling/make_sheets.py <folder> --count 1000` puts 1000 LPC front views on
   63 numbered sheets of 16 and writes `key.json` with each one's true label.
2. 5 Haiku 5.5 agents (medium effort), 12-13 sheets each, write one label per character with the
   prompt in [prompt.md](prompt.md).
3. `python3 labelling/compare.py <folder> <labels subfolder>` checks each label against the truth.

## Results on the same 1000 LPC characters (2026-11-23)

| | Prompt v1 | Prompt v2 |
|---|---|---|
| Labels with at least one wrong fact | 254 (25.4%) | 145 (14.5%) |
| Missed a dagger (118 have one) | 118 | 100 |
| Man/woman wrong | 78 of 160 said | not said (v2 forbids it) |
| Body wrong (skeleton, orc, elf, human) | 52 | 30 |
| Hair colour wrong | 18 | 18 |
| Named a spear or shield that is not there | 8 | 4 |
| Cost at API prices (Haiku 5.5: $0.10 / $0.50 per M tokens) | $0.18 | $0.21 |

v2 tells the labeller not to guess man or woman (at 64 pixels it was right only half the time), to
call bones a skeleton and to name skin colours instead of "pale". The small LPC dagger at the hip
is still missed most of the time. At v2 prices all 50,000 LPC characters cost about $10 and all
14,202 pac characters about $3; 5 agents label about 1000 in 2.5 minutes.

## pac, labelled (2026-11-23)

All 14,153 pac characters in the export (train, val and test) are labelled with prompt v2, adjusted
for pac's two styles (it says "a small chibi character" for a big head on a small body, and names
ears, horns, bows and hair clips). 69 Haiku 5.5 jobs of 13 sheets, 5 at a time, took 32 minutes
and about $2.64 at API prices.

```bash
uv run python labelling/make_sheets.py data/labels/pac --source pac --split all --count 0
python3 labelling/collect.py data/labels/pac      # -> data/labels/pac/labels.jsonl
```

`labels.jsonl` has one line per character: `{"character": "pac/train/0", "label": "..."}`. One job
numbered its cells 1-16 on each sheet instead of with the cell numbers; `collect.py` maps those back
by position. There is no true label to check pac against, so expect about the LPC test's error rate
(14.5% of labels with a wrong fact, mostly missed small daggers). pac is CC-BY-NC-4.0: a model
trained on it is for testing, not for a game that is sold.
