# Dataset

Downloads the image data for the engine and shows it on a dashboard. Cleaning, labelling and
splitting come next, each as its own folder beside `gather/`, and each adds its view to the
same dashboard.

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
uv run pixel dashboard                        # build the dashboard
open data/reports/dashboard.html              # look at it
```

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
  gather/                    step 1: download the sources
  dashboard/                 the page that shows what you have
tests/                       tests for all of the above
data/raw/<id>/               downloads, never edited (not in git)
data/raw/_experimental/      sources for the experimental model only, never shipped
data/reports/                the dashboard and its preview pictures
```

`use` in `sources.json` is `train`, `eval` (test set) or `experimental`. To add a source, add an
entry there with the exact `revision` (commit), so a later download gets the same files.
