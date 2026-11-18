# Training

Tries, trains and evaluates the models of the engine. It reads the dataset's data folder
(`../dataset/data` by default, or `--data`).

## Step 1: try existing models, no training

`pixel-train tryout` runs existing models on test prompts (create: text to character) and on test
characters from an export (rotate: front view to left, back and right, by asking the model to edit
the front view). Every picture is also snapped to a 64x64 sprite: the most common colour in each
block, at most 32 colours, and the background that touches the border made transparent.

| Model | Repo | Licence |
|---|---|---|
| `flux3-klein` | black-forest-labs/flux-3-image-klein | FLUX Kommunity License: selling a fine-tuned version needs BFL's separate licence |
| `flux2-klein-4b` | black-forest-labs/FLUX.2-klein-4B | Apache-2.0 |

`flux3-klein` runs without its prompt upsampler, so the prompts are used as written.

### On the Mac (once)

```bash
brew install uv
cd pixel-ai-engine/training
uv sync --extra models
uv run hf auth login
```

The login asks for a token from https://huggingface.co/settings/tokens (read access is enough), on
the account that accepted the FLUX 3 Klein licence.

### Run

```bash
uv run pixel-train tryout                              # both models, 10 prompts x 2 seeds, 4 test characters
uv run pixel-train tryout --models flux2-klein-4b      # one model
uv run pixel-train tryout --seeds 1 --rotate 2         # a quick, smaller run
```

The first run downloads each model, tens of GB, into the Hugging Face cache. Results go to
`../dataset/data/tryouts/<name>/`; look at them with `uv run pixel browse` in `dataset/`, under
Try-outs. Results are written after each model, so if the second model fails, the first one's
pictures are kept.

The prompts are in `prompts.json`.

## Tests

```bash
uv run pytest
```

The tests use a stand-in for the models, so they run without `--extra models`.
