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
| `flux2-klein-base-4b` | black-forest-labs/FLUX.2-klein-base-4B | Apache-2.0 |

`flux2-klein-4b` makes a picture in 4 steps. `flux2-klein-base-4b` is the same model before that
speed-up: 28 steps with guidance (two passes a step), so it is several times slower, and it is the
one made for training. It shares the text encoder and VAE of `flux2-klein-4b`, so only its
transformer (7.75 GB) is downloaded:

```bash
uv run hf download black-forest-labs/FLUX.2-klein-base-4B --include "transformer/*" "scheduler/*" "model_index.json"
```

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
`../dataset/data/tryouts/<name>/`; look at them in the dashboard's Library, under Try-outs. Results are written after each model, so if the second model fails, the first one's
pictures are kept.

The prompts are in `prompts.json`.

## Step 2: train a LoRA for rotate

`pixel-train train` teaches FLUX.2 Klein 4B Base to turn a front view into the left, back and right
views. It trains a LoRA: a small set of extra weights next to the frozen model, so it fits on a
32 GB Mac and writes a file of tens of MB.

Each training example is the front view of a character from the export's train split, the
instruction for a view from `prompts.json`, and the real view to make. The sprites are scaled up
to 512 pixels on white, as in the try-out. Every `--every` steps it measures the loss on fixed
pairs from the val split (the same noise each time, so the numbers compare) and saves a
checkpoint. Lower is better.

It needs the export (`uv run pixel export` in `dataset/`) and the model in the Hugging Face cache.

The first run, `rotate-v1`, trained the 4-step model (`--model flux2-klein-4b`). It halved the
difference to the real views on the test characters, but its pictures came out soft: more sampling
steps and the front view's colours did not make the shapes sharp again. Training the 4-step model
undoes part of its speed-up, so the base model is now the default.

```bash
uv run pixel-train train --name first --steps 20 --every 10          # a short run, to see the speed
uv run pixel-train train --name rotate-v1                            # 1,000 steps of 4 pairs
uv run pixel-train train --name rotate-v1 --steps 2000 --resume      # go on from the last checkpoint
uv run pixel-train train --name lpc-only --sources lpc-4view         # one source only
```

The run goes to `../dataset/data/runs/<name>/`: `log.jsonl` (the loss of every step),
`checkpoints/step-*/` and `final/`. If the run stops (the Mac sleeps, Ctrl+C), `--resume` with the
same `--name` goes on from the last checkpoint and sees the same pairs an unbroken run would.

Try the result on the test characters, next to the model without it:

```bash
uv run pixel-train tryout --models flux2-klein-base-4b --lora ../dataset/data/runs/rotate-v2
uv run pixel-train tryout --models flux2-klein-base-4b --lora ../dataset/data/runs/rotate-v2/checkpoints/step-000500
uv run pixel-train tryout --models flux2-klein-base-4b --size 512 --name base-512     # without the LoRA
```

A try-out with a LoRA makes pictures at the size the LoRA was trained at; `--size` and `--steps`
change the size and the sampling steps. To try only the rotations, point `--prompts` at a copy of
`prompts.json` with no create subjects.

Once the model is downloaded, nothing needs the internet. Put `HF_HUB_OFFLINE=1` before a command to
be sure it does not look online.

Licences: `pac` is CC-BY-NC-4.0, so a LoRA trained on it is for non-commercial use. `--sources
lpc-4view` trains on the CC-BY-SA-3.0 characters only.

## Step 3: text to a character in 4 views

`pixel-train generate` draws a character from your words, then turns it with a trained LoRA:

```bash
uv run pixel-train generate "a knight with a blue cape" --lora ../dataset/data/runs/rotate-v2
uv run pixel-train generate "a frog wizard" --seeds 4                  # front views only, no turning
```

The front view comes from `--front-model` (the 4-step model by default, at 1024 pixels) with the
sprite wording of `prompts.json` around your words (`--raw` uses them as written). The LoRA was
trained to turn a front view, not to draw from text, so it is used only for the left, back and
right views, with the model and size it was trained at (`--turn-model` and `--steps` change that).

Each view is snapped to a 128x128 sprite (`--sprite`). The model draws finer than 64 pixels, and
at 64 the faces and small parts were lost. The LoRA learnt on 64-pixel sprites at 256 pixels, so
a 128 sprite is turned at 512 pixels, where its pixels are blocks of the same size; that kept the
faces on the side views, where turning it at 256 did not. The results go to
`../dataset/data/generated/<date>-<prompt>/`: `s0-front.png`, `s0-left.png` and so on, the raw
pictures, and `s0-sheet.png` with the 4 views side by side.

The snap keeps at most 32 colours. `--palette` snaps every pixel to a classic palette instead
(`pico-8`, `game-boy`, `nes`, `commodore-64`, `zx-spectrum`, `cga`, `1-bit`; the colours are
Lospec's), and `--colours` (2 to 64) limits each sprite to that many, counting only the character,
not the cleared background. With a palette, the most used of its colours are kept. The palette is
put on after the model draws, so a 4-colour palette can merge small details:

```bash
uv run pixel-train generate "a frog wizard" --palette pico-8 --colours 12
```

### Turn front views you already have

`pixel-train rotate` turns front views that are already made, with a rotate LoRA, and leaves the
drawing out:

```bash
uv run pixel-train rotate knight --lora rotate-v2                       # every character in data/generated/knight
uv run pixel-train rotate knight --lora pixie-turn-v1 --seeds 1         # one character
uv run pixel-train rotate my-hero.png --lora rotate-v2 --views back     # a PNG of your own, only its back
```

The source is a folder from `generate` (or its name under `data/generated`) or a PNG. `--lora` is
required and must be a rotate LoRA. `--turn-model`, `--sprite`, `--turn-size` and `--steps` work as
in `generate`; `--views` picks some of left, back and right (all three by default).

The results go to a new folder, `../dataset/data/generated/<date>-turned-<source>/` (or `--name`),
in the layout `generate` writes: each front view keeps its seed (`s1-front.png` stays `s1`), then
`s1-left.png` and so on, the raw pictures, `s1-sheet.png` and `generated.json`, whose
`rotated_from` names the source. So the dashboard's Create, Rotate, Animate and Library screens
show it as they show a generated character. A PNG is put in the middle of a clear square; one
bigger than `--sprite` is snapped to it, a smaller one is kept as it was drawn.

### A create LoRA: draw the front view in your own style

The plain model draws the front view as it is. A create LoRA teaches it to draw like the training
characters. It trains on the captions of the export: each character's caption in, its front view
out. lpc-4view has captions from its art layers (45,016 training characters). A character without
one takes its AI label from `../dataset/data/labels/<name>/labels.jsonl`, if it has one: pac is
labelled by Haiku 5.5 (10,898 training characters; see `../dataset/labelling/`).

The licence follows the sources: lpc-4view is CC-BY-SA-3.0 (credit the LPC artists), pac is
CC-BY-NC-4.0, so a LoRA with pac in it is for testing, not for a game that is sold. For a LoRA you
can sell with, train on lpc-4view only:

```bash
HF_HUB_OFFLINE=1 caffeinate -i uv run pixel-train train --task create --name create-v1 --size 256 --steps 2000 --sources lpc-4view
HF_HUB_OFFLINE=1 caffeinate -i uv run pixel-train train --task create --name create-mix --size 256 --steps 2000   # with pac
uv run pixel-train generate "a frog wizard" --create-lora create-v1 --lora rotate-v2
```

LPC alone draws everything in the LPC way. pac gives more styles but is non-commercial. For more
styles you can sell with, add the OpenGameArt sprites (CC0, about 1,300 characters cut from packs and
labelled by Haiku; see `../dataset/opengameart/README.md`). They are their own export, so add it with
`--more-exports`; it is small next to LPC, so `--more-repeat` shows each of its characters more often:

```bash
HF_HUB_OFFLINE=1 caffeinate -i uv run pixel-train train --task create --name create-v2 --size 256 --steps 2000 --sources lpc-4view opengameart-2d --more-exports opengameart-v1-data --more-repeat 5
```

Each caption is put in the same words `generate` puts around your prompt (the `create` template
of `prompts.json`), so the LoRA learns the words it will be asked with. There is a caption per
character, too many to turn into embeddings up front, so the text model (8 GB) stays loaded and
encodes each caption as it comes. On an M1 Max that is about 35 s per step at 256 pixels.

A create run learns the front view and the side view (`--views front side`, the default). The side
is each character's right view, captioned "side view, facing right", so `generate --facing side
--create-lora` draws it and flips it for the left. Exports with front views only, such as
OpenGameArt, give front pairs only. A run keeps the views it started with when it goes on; a run
from before side views (no `views` in its `run.json`) learnt the front only, and `generate` and the
dashboard draw its side views with none.

With `--create-lora`, the front view is drawn at the LoRA's size scaled with `--sprite` (512 for a
128 sprite), as for turning. `--lora` must be a rotate LoRA and `--create-lora` a create one;
`generate` stops if they are the other way round. `--resume` needs the run's own `--task`.

### Model names

Every model is a Pixie, named for its job. The number goes up when the recipe changes (other data,
other sources or repeats, other settings). The daily checkpoints (`step-000500`, `step-001000`, ...)
are the steps inside one version.

| Name | Job | `--task` |
|---|---|---|
| `pixie-draw-v1` | words to a character's front or side view | `create` |
| `pixie-turn-v1` | front view to the left, back and right views | `rotate` |
| `pixie-animate-v1` | a sprite to the frames of an action | (to be built) |
| `pixie-draw-object-v1` | words to an object or icon | `create`, own export |

Two older runs are kept: `rotate-v2` (the turning model until `pixie-turn-v1` is better) and `create-v1` (LPC only, the one create LoRA you can sell with).

### One create LoRA on all character data, a little each day

`characters-v2-data` is the export with every character source that has 4 views: lpc-4view, pac and
pixellab (moss-64 is only in its test split). With the OpenGameArt export next to it, that is all
the character data:

```bash
cd dataset && uv run pixel export characters-v2-data && cd ../training
```

Run the same command every day. `--add-steps 500` trains 500 more steps than the last checkpoint
(it starts the run the first time). 500 steps of 4 pairs is 2,000 pictures, about 4 hours at 256
pixels on an M1 Max:

```bash
HF_HUB_OFFLINE=1 caffeinate -i uv run pixel-train train --task create --name pixie-draw-v1 --export characters-v2-data --size 256 --more-exports opengameart-v1-data --repeat opengameart-2d=5 pixellab=10 --add-steps 500
```

`--repeat` shows a small source more often (`pixellab=10`: each of its characters 10 times), or a
big one less (`lpc-4view=0.5`: a fixed half). The run goes through every pair once, in a shuffled
order, before any comes back; the log and the screen say how much of the data it has seen. Keep the
command the same each day: other sources or repeats make another set of pairs, and so another order.

The same run from the dashboard's Training screen: name it `pixie-draw-v1`, pick Create, the export
`characters-v2-data`, check `opengameart-v1-data` under More exports, set opengameart-2d to ×5 and
pixellab to ×10, and Steps to 500. Each day after, select the run and press Add 500 steps.

Try it at any time with `uv run pixel-train generate "a frog wizard" --create-lora pixie-draw-v1`.

Licences: pac (CC-BY-NC-4.0) and pixellab (PixelLab's permission: local use, no commercial app) make
this LoRA non-commercial. For one you can sell with, train on lpc-4view and OpenGameArt only.

atlas-1.4m, icons-172k, pixelart-308k and landscapes-20k are not in it. They are objects, icons and
scenes, not characters. In a character LoRA they would teach it to draw a chair when you ask for a
knight. They fit a LoRA of their own (icons, scenes), with their own words.

## Step 4: animate a character (try-out)

`pixel-train animate` gives a sprite from `generate`, or a PNG of your own, to Wan 2.2 image-to-video with the
[pixel-animate LoRA](https://huggingface.co/styly-agents/Wan2-2-pixel-animate) (Apache-2.0, trained
on 226 pixel sprite animations). It copies that LoRA's own ComfyUI workflow: the LoRA on both
experts, the lightx2v 4-step speed-up LoRA, guidance 1, shift 5.

Wan 2.2 I2V A14B is two 14B experts, about 56 GB at full size. On a 32 GB Mac they run as 4-bit
GGUF files from `QuantStack/Wan2.2-I2V-A14B-GGUF`. With its LoRAs one expert takes about 13 GB;
both at once pushed the Mac into swap. So only one model is in memory at a time: the text encoder
(11 GB) encodes all prompts and is let go, the high-noise expert does its 2 steps for every clip
and is let go, then the low-noise expert finishes every clip.

On an M1 Max (32 GB) a 33-frame clip takes about 11 minutes at 384 pixels (the default) and 15 at
512. Once snapped to 64x64 the two look the same.

Download once, about 36 GB (use Wi-Fi):

```bash
uv sync --extra models
uv run hf download styly-agents/Wan2-2-pixel-animate wan2.2_animate_adapter_model.safetensors
uv run hf download lightx2v/Wan2.2-Lightning --include "Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/*.safetensors"
uv run hf download Wan-AI/Wan2.2-I2V-A14B-Diffusers --include "model_index.json" "scheduler/*" "text_encoder/*" "tokenizer/*" "vae/*" "transformer/config.json" "transformer_2/config.json"
uv run hf download QuantStack/Wan2.2-I2V-A14B-GGUF HighNoise/Wan2.2-I2V-A14B-HighNoise-Q4_K_M.gguf LowNoise/Wan2.2-I2V-A14B-LowNoise-Q4_K_M.gguf
```

Run:

```bash
uv run pixel-train animate knight --seeds 0 --views right --actions walk --frames 17   # one short clip, to see the speed
uv run pixel-train animate knight                                                      # idle and walk, front and right
uv run pixel-train animate knight --subject "a knight in grey armour with a blue cape, empty hands"
uv run pixel-train animate knight --pixel-strength 0 --name knight-no-lora              # the same without the LoRA
uv run pixel-train animate my-hero.png --subject "a hero in a red coat" --views right   # a PNG of your own
```

A PNG of your own needs `--subject` (what it shows) and one `--views` (the way it faces; front if
left out). A tall or wide PNG is put in the middle of a clear square. Each frame is snapped back to
the PNG's own size, up to 128 pixels; a bigger picture is snapped to 128.

The prompt uses the words the character was made from. The model draws in anything those words
name, even when the sprite does not show it (a sword in the words gave the knight a sword). Give
`--subject` to describe only what the sprite shows.

Idle and walk are given the sprite as the first and the last frame (Wan's first-last-frame mode),
so the clip must come back to it. The clip is cut at the frame closest to the first one again, so
the GIF and sheet loop. `--open-end` gives only the first frame, as before. Attack never gets a
last frame.

Results go to `../dataset/data/animated/<name>/`, per clip: `<id>-raw.gif` (the video as made),
`<id>.gif` (every frame snapped to a 64x64 sprite in the input sprite's colours) and
`<id>-sheet.png` (`--keep` evenly spaced frames side by side).

## Tests

```bash
uv run pytest
```

The tests use a stand-in for the models and for training, so they run without `--extra models`.
