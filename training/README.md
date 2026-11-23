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
`../dataset/data/tryouts/<name>/`; look at them with `uv run pixel browse` in `dataset/`, under
Try-outs. Results are written after each model, so if the second model fails, the first one's
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

### A create LoRA: draw the front view in your own style

The plain model draws the front view as it is. A create LoRA teaches it to draw like the training
characters. It trains on the captions of the export: each character's caption in, its front view
out. Only lpc-4view has captions (45,016 training characters), so a create LoRA draws LPC-style
characters, 64-pixel sprites, and its licence is CC-BY-SA-3.0 (credit the LPC artists).

```bash
HF_HUB_OFFLINE=1 caffeinate -i uv run pixel-train train --task create --name create-v1 --size 256 --steps 2000
uv run pixel-train generate "a frog wizard" --create-lora ../dataset/data/runs/create-v1 --lora ../dataset/data/runs/rotate-v2
```

Each caption is put in the same words `generate` puts around your prompt (the `create` template
of `prompts.json`), so the LoRA learns the words it will be asked with. There is a caption per
character, too many to turn into embeddings up front, so the text model (8 GB) stays loaded and
encodes each caption as it comes. On an M1 Max that is about 35 s per step at 256 pixels.

With `--create-lora`, the front view is drawn at the LoRA's size scaled with `--sprite` (512 for a
128 sprite), as for turning. `--lora` must be a rotate LoRA and `--create-lora` a create one;
`generate` stops if they are the other way round. `--resume` needs the run's own `--task`.

## Step 4: animate a character (try-out)

`pixel-train animate` gives a sprite from `generate` to Wan 2.2 image-to-video with the
[pixel-animate LoRA](https://huggingface.co/styly-agents/Wan2-2-pixel-animate) (Apache-2.0, trained
on 226 pixel sprite animations). It copies that LoRA's own ComfyUI workflow: the LoRA on both
experts, the lightx2v 4-step speed-up LoRA, guidance 1, shift 5.

Wan 2.2 I2V A14B is two 14B experts, about 56 GB at full size. On a 32 GB Mac they run as 4-bit
GGUF files from `QuantStack/Wan2.2-I2V-A14B-GGUF`. The text encoder (11 GB) encodes all prompts
first and is then let go, so it is never in memory with the experts.

Download once, about 33 GB (use Wi-Fi):

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
uv run pixel-train animate knight --pixel-strength 0 --name knight-no-lora              # the same without the LoRA
```

Results go to `../dataset/data/animated/<name>/`, per clip: `<id>-raw.gif` (the video as made),
`<id>.gif` (every frame snapped to a 64x64 sprite in the input sprite's colours) and
`<id>-sheet.png` (`--keep` evenly spaced frames side by side).

## Tests

```bash
uv run pytest
```

The tests use a stand-in for the models and for training, so they run without `--extra models`.
