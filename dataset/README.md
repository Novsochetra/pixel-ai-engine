# Dataset

Turns the downloaded image data into one list of records, one per image, that every later step
reads: which character it is, which view, its size, source and licence. Steps so far:

1. **gather** ✅ download the sources (`pixel gather`) and import them into records (`pixel import`).
2. **analyze** ✅ measure each image and flag bad ones (`pixel analyze`).
3. **annotate**: captions. Later, for the create task: rotation does not need them.
4. **export** ✅ fix, split by character and write the training files (`pixel export`).

`pixel browse` shows the records in your web browser and grows a view with each step.

## Setup on a Mac (once)

```bash
brew install uv
cd pixel-ai-engine/dataset
uv sync
```

Run every command below from this `dataset/` folder.

Keep the data out of iCloud-synced folders (Desktop, Documents): it is about 53 GB in total.
By default it goes to `dataset/data/`, which git ignores. To put it somewhere else, such as an
external SSD:

```bash
export PIXEL_DATA=/Volumes/MySSD/pixel-engine
```

## Use

```bash
uv run pixel list --sizes                     # every source, its size and whether you have it
uv run pixel gather lpc-4view pac moss-64     # download some sources by name
uv run pixel gather --all                     # everything except experimental sources (~50 GB)
uv run pixel gather --all --experimental      # everything
uv run pixel dashboard                        # a page of previews of each download
open data/reports/dashboard.html              # look at it

uv run pixel import pac lpc-4view             # turn downloads into records (importers: pac, lpc-4view)
uv run pixel analyze                          # measure every imported image and flag bad ones
uv run pixel export                           # write data/exports/rotation-v1 for training
uv run pixel browse                           # open the records in your browser
```

`pixel browse` runs a small web app at http://127.0.0.1:8777 that only your own computer can open.
It lists every imported character with its views side by side, filters by source, split and
caption text, and shows each image's record. Flagged shows the images the analyzer flagged, by
reason, so you can check its decisions. Exports shows each export's split counts, its leak check
and sample characters. Try-outs shows what existing models made in `training/`, next to the
real views. Stop it with Ctrl+C.

Training and Generate run `pixel-train` (in `training/`, which needs `uv sync --extra models` once)
from the browser, offline:

- **Training** lists every run with its progress and a chart of its check score. It starts a new
  run (task rotate or create), resumes one to more steps, and tries a rotate checkpoint on the test
  characters (the result shows under Try-outs). A create run is tried on the Generate page.
- **Generate** draws a character from your words, with a create LoRA or the plain model, and
  turns it with a rotate LoRA. Everything it made is listed below the form.

One job runs at a time, since each fills most of a 32 GB Mac; its output shows at the top of both
pages, with a Stop button. Each job keeps its settings and output in `data/jobs/`. Stopping the
dashboard stops its job too, so keep it open while training. Only pages of the dashboard itself
can start a job.

A download that stops halfway picks up where it left off when you run it again.

Two sources are downloaded by hand: `itch-8dir-cc0` and `spritedatabase`. Run
`uv run pixel gather itch-8dir-cc0` to get the links and its folder, put the files there, then run
`uv run pixel dashboard`.

## Tests

```bash
uv run pytest
```

## What is where

```
sources.json                 every source: where it comes from, its exact version, licence, use, tasks
src/pixel_data/
  cli.py                     the `pixel` command
  sources.py                 reads sources.json and knows where each source's files live
  gather/                    step 1: download the sources, and importers/ that turn each into records
  analyze/                   step 2: measure each image (measure.py), flag it (rules.py), find copies
  export/                    step 4: pick characters (select.py), fix (fix.py), split (split.py), write
  dashboard/                 the downloads page and the `pixel browse` app
  records.py                 the record store: one row per image in data/records.sqlite
  images.py                  loads a record's picture from the original download
tests/                       tests for all of the above
data/raw/<id>/               downloads, never edited (not in git)
data/raw/_experimental/      sources for the experimental model only, never shipped
data/records.sqlite          the records (not in git); open it with any SQLite viewer
data/reports/                the downloads page and its preview pictures
data/exports/<name>/         training files: PNGs, characters.jsonl, export.json (not in git)
```

`use` in `sources.json` is `train`, `eval` (test set) or `experimental`. To add a source, add an
entry there with the exact `revision` (commit), so a later download gets the same files.

## Records

A record does not copy the picture: it points at it inside the original download (`file`, the
`member` inside a zip or tar, and a `crop` box when one picture holds several views). So the raw
downloads stay as they are, and nothing takes disk space twice.

Views are named `front`, `back`, `left` and `right` (the way the character faces on screen), plus
`front-left`, `front-right`, `back-left` and `back-right` for 8-direction sources. A `character`
groups every view of one character; the later train/test split keeps a character on one side.

## Analysis

`pixel analyze` gives every image a status, from the worst of its flags:

| Status | Meaning |
|---|---|
| ok | ready to use |
| fix | a later step can repair it on its own (snap half-transparent pixels, shrink art drawn at 2x) |
| check | a person should look: it may be cut off or may not be pixel art |
| drop | left out: empty, almost empty, or an exact copy of another character |

The flags and their limits are all in `src/pixel_data/analyze/rules.py`. Near-identical characters
stay in but form a group, as do characters that share even one identical view (base bodies that
differ only in the face), so the split puts the whole group on one side.

## Export

`pixel export [name]` (default `rotation-v1`) writes `data/exports/<name>/`:

- `images/<split>/<source>/<character>/<view>.png`, fixed: half-transparent pixels snapped to solid
  or clear, art drawn at 2x shrunk to its true size,
- `characters.jsonl`, one line per character with its split and the path of each view,
- `export.json`, what went in, what was left out and why, the dataset versions, and the leak check.

A character goes in when it has all four views, none dropped and none marked check (add
`--include-check` to take those too). Experimental sources stay out unless you add `--experimental`.

The split is by group, 90% train, 5% val, 5% test, from a hash of the group's name, so a character
keeps its split when new data is added. A source's own test set (PAC's) stays test.
