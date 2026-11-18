# Dataset

Turns the downloaded image data into one list of records, one per image, that every later step
reads: which character it is, which view, its size, source and licence. Steps so far:

1. **gather** ✅ download the sources (`pixel gather`) and import them into records (`pixel import`).
2. **analyze**: measure each image and flag bad ones. Next.
3. **annotate**: captions.
4. **export**: split by character and write training files.

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
uv run pixel browse                           # open the records in your browser
```

`pixel browse` runs a small web app at http://127.0.0.1:8777 that only your own computer can open.
It lists every imported character with its views side by side, filters by source, split and
caption text, and shows each image's record. Stop it with Ctrl+C.

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
  dashboard/                 the downloads page and the `pixel browse` app
  records.py                 the record store: one row per image in data/records.sqlite
  images.py                  loads a record's picture from the original download
tests/                       tests for all of the above
data/raw/<id>/               downloads, never edited (not in git)
data/raw/_experimental/      sources for the experimental model only, never shipped
data/records.sqlite          the records (not in git); open it with any SQLite viewer
data/reports/                the downloads page and its preview pictures
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
