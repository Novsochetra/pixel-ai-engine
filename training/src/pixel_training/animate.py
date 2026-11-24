"""A character sprite to a short animation: Wan 2.2 image-to-video with the pixel-animate LoRA.

Wan 2.2 I2V A14B has two experts of 14B each: the high-noise one lays out the motion in the first
steps, the low-noise one draws the detail in the last steps. At full size they take about 56 GB, so
on a 32 GB Mac they are loaded as 4-bit GGUF files (about 10 GB each). The setup follows the
pixel-animate LoRA's own ComfyUI workflow: the LoRA on both experts, a 4-step speed-up LoRA
(lightx2v Lightning) on both, guidance 1, shift 5, two steps per expert.

With its LoRAs one expert takes about 13 GB; both at once push a 32 GB Mac into swap, which made a
step take minutes. So the clips are made in two phases: the high-noise expert does its steps for
every clip, is let go, then the low-noise expert finishes every clip. Only one is in memory at a time.

A video model does not keep the pixel grid, so every frame is snapped back to a sprite with the
colours of the input sprite. Looping actions (idle, walk) are given the sprite as the last frame
too (Wan's first-last-frame mode), so the clip must come back to it; the loop is cut where the
motion is closest to the first frame again, and a few evenly spaced frames of that make the sheet.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from PIL import Image, ImageChops, ImageStat

from pixel_training.pixelate import block_mode, blow_up, clear_background, palette_of

BASE_REPO = "Wan-AI/Wan2.2-I2V-A14B-Diffusers"
GGUF_REPO = "QuantStack/Wan2.2-I2V-A14B-GGUF"
PIXEL_LORA = ("styly-agents/Wan2-2-pixel-animate", "wan2.2_animate_adapter_model.safetensors")
LIGHTNING_REPO = "lightx2v/Wan2.2-Lightning"
LIGHTNING_DIR = "Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1"

SPRITE = 64
# The largest sprite a frame is snapped to: a bigger picture is not pixel art, so it becomes this size.
LARGEST_SPRITE = 128
# GIFs and sheets show every sprite at this size.
SHOW = 256
FPS = 16
# A loop is at least this many frames, so a still second frame does not count as "back to the start".
SHORTEST_LOOP = 8

# What each action asks for, and whether it loops. The subject is what the sprite shows.
ACTIONS = {
    "idle": ("idle animation: stands in place and breathes, the chest and head move a little up and down, "
             "then comes back to the first pose", True),
    "walk": ("walk cycle in place: one leg steps forward, then the other leg steps forward, the arms swing, "
             "then comes back to the first pose. The character stays in the center of the frame", True),
    "attack": ("attack animation: swings forward and returns to the first pose", False),
}
VIEW_WORDS = {"front": "facing the viewer", "left": "facing left, side view", "back": "seen from the back",
              "right": "facing right, side view"}
TEMPLATE = ("pixel art game sprite animation of {subject}, {view}. {action}. Crisp pixel art, the same character "
            "with the same clothes and items in every frame, plain flat white background, the camera does not move")

# The frames for each (prompt, first picture, seed, last picture or None), in order, as each clip is done.
AnimateAll = Callable[[list[tuple[str, Image.Image, int, Image.Image | None]]], Iterator[list[Image.Image]]]


@dataclass(frozen=True)
class Job:
    id: str
    sprite: Path
    prompt: str
    seed: int
    loops: bool


def jobs_for(source: Path, seeds: list[int], views: list[str], actions: list[str], subject: str | None = None) -> list[Job]:
    """One job per seed, view and action, from the sprites `pixel-train generate` wrote.

    The subject defaults to the words the character was made from; give it to describe only what the
    sprite shows (a weapon in the words but not in the picture gets drawn in).
    """
    subject = subject or json.loads((source / "generated.json").read_text())["prompt"]
    jobs = []
    for seed in seeds:
        for view in views:
            sprite = source / f"s{seed}-{view}.png"
            if not sprite.exists():
                continue
            for action in actions:
                words, loops = ACTIONS[action]
                prompt = TEMPLATE.format(subject=subject, view=VIEW_WORDS[view], action=words)
                jobs.append(Job(f"s{seed}-{view}-{action}", sprite, prompt, seed, loops))

    return jobs


def image_jobs(image: Path, subject: str, view: str, actions: list[str], seeds: list[int]) -> list[Job]:
    """Jobs for one PNG of your own: you say what it shows and which way it faces."""
    jobs = []
    for seed in seeds:
        for action in actions:
            words, loops = ACTIONS[action]
            prompt = TEMPLATE.format(subject=subject, view=VIEW_WORDS[view], action=words)
            jobs.append(Job(f"s{seed}-{view}-{action}", image, prompt, seed, loops))

    return jobs


def square(sprite: Image.Image) -> Image.Image:
    """The sprite in the middle of a clear square, so a tall or wide one is not stretched."""
    sprite = sprite.convert("RGBA")
    if sprite.width == sprite.height:
        return sprite

    side = max(sprite.size)
    page = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    page.alpha_composite(sprite, ((side - sprite.width) // 2, (side - sprite.height) // 2))

    return page


def difference(a: Image.Image, b: Image.Image) -> float:
    """Mean colour difference of two sprites on white, 0 when they are the same."""
    def flat(sprite):
        page = Image.new("RGBA", sprite.size, (255, 255, 255, 255))
        page.alpha_composite(sprite.convert("RGBA"))
        return page.convert("RGB")

    return sum(ImageStat.Stat(ImageChops.difference(flat(a), flat(b))).mean)


def cycle(sprites: list[Image.Image], shortest: int = SHORTEST_LOOP) -> list[Image.Image]:
    """The frames from the first one up to where the motion is closest to the first one again."""
    if len(sprites) <= shortest:
        return list(sprites)

    end = min(range(shortest, len(sprites)), key=lambda index: difference(sprites[index], sprites[0]))

    return list(sprites[:end])


def pick(frames: list, count: int) -> list:
    """`count` evenly spaced frames from the first one."""
    if count >= len(frames):
        return list(frames)

    return [frames[round(index * len(frames) / count)] for index in range(count)]


def snap(frame: Image.Image, palette: Image.Image, size: int = SPRITE) -> Image.Image:
    """A video frame back to a sprite in the input sprite's colours, so frames do not flicker."""
    return clear_background(block_mode(frame, size, palette))


def save_gif(sprites: list[Image.Image], path: Path, fps: int) -> None:
    size = SHOW
    frames = []
    for sprite in sprites:
        flat = Image.new("RGBA", sprite.size, (255, 255, 255, 255))
        flat.alpha_composite(sprite.convert("RGBA"))
        frames.append(flat.convert("RGB").resize((size, size), Image.NEAREST))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=round(1000 / fps), loop=0)


def save_strip(sprites: list[Image.Image], path: Path) -> None:
    size = SHOW
    strip = Image.new("RGBA", (size * len(sprites), size), (255, 255, 255, 255))
    for index, sprite in enumerate(sprites):
        strip.alpha_composite(sprite.convert("RGBA").resize((size, size), Image.NEAREST), (index * size, 0))
    strip.save(path)


def run(folder: Path, jobs: list[Job], animate_all: AnimateAll, size: int, keep: int, info: dict | None = None,
        fps: int = FPS, same_end: bool = True) -> list[dict]:
    """Animate every job; keep the raw video as a GIF, the snapped loop as a GIF, and a sheet of `keep` frames.

    With `same_end`, a looping action gets the sprite as its last frame too. With `info`,
    animated.json is written after every clip, so a crash keeps what is done.
    """
    folder.mkdir(parents=True, exist_ok=True)
    sources = [square(Image.open(job.sprite)) for job in jobs]
    inputs = []
    for job, source in zip(jobs, sources):
        picture = blow_up(source, size)
        inputs.append((job.prompt, picture, job.seed, picture if job.loops and same_end else None))

    rows = []
    for job, source, (*_, last), frames in zip(jobs, sources, inputs, animate_all(inputs)):
        small = [frame.convert("RGB").resize((256, 256), Image.LANCZOS) for frame in frames]
        small[0].save(folder / f"{job.id}-raw.gif", save_all=True, append_images=small[1:],
                      duration=round(1000 / fps), loop=0)

        palette = palette_of(source)
        sprites = [snap(frame, palette, min(source.width, LARGEST_SPRITE)) for frame in frames]
        # The first frame of the video is the input picture itself; a loop starts there. With the same
        # last frame, the last one is the first again, so the cut drops it.
        used = cycle(sprites) if job.loops else sprites[1:]
        save_gif(used, folder / f"{job.id}.gif", fps)

        chosen = pick(used, keep)
        save_strip(chosen, folder / f"{job.id}-sheet.png")
        rows.append({"id": job.id, "sprite": str(job.sprite), "prompt": job.prompt, "seed": job.seed,
                     "same_end": last is not None, "frames": len(frames), "used": len(used),
                     "kept": len(chosen)})
        if info is not None:
            write_info(folder, {**info, "clips": rows})

    return rows


def write_info(folder: Path, info: dict) -> None:
    info = {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **info}
    (folder / "animated.json").write_text(json.dumps(info, indent=2))


def wan_animator(prompts: list[str], device: str, size: int, frames: int, steps: int, quant: str,
                 lightning: bool, pixel_strength: float, log: Callable[[str], None] = print) -> AnimateAll:
    """Wan 2.2 I2V A14B where the text encoder and each expert are in memory one at a time."""
    import time

    import torch
    from diffusers import FlowMatchEulerDiscreteScheduler, GGUFQuantizationConfig, WanImageToVideoPipeline, WanTransformer3DModel
    from huggingface_hub import hf_hub_download

    from pixel_training.models import free_memory

    dtype = torch.bfloat16
    pipe = WanImageToVideoPipeline.from_pretrained(BASE_REPO, transformer=None, transformer_2=None, dtype=dtype)

    # The text encoder (UMT5-XXL, 11 GB) is used once for all prompts, then let go.
    pipe.text_encoder.to(device)
    guidance = 1.0 if lightning else 3.5
    embeds = {}
    with torch.no_grad():
        for prompt in dict.fromkeys(prompts):
            # 512 tokens, as the pipeline itself encodes.
            positive, negative = pipe.encode_prompt(prompt, negative_prompt="", do_classifier_free_guidance=guidance > 1,
                                                    max_sequence_length=512, device=device, dtype=dtype)
            embeds[prompt] = (positive.cpu(), None if negative is None else negative.cpu())
    pipe.register_modules(text_encoder=None)
    free_memory()

    pipe.vae.to(device)
    pipe.scheduler = FlowMatchEulerDiscreteScheduler.from_config(pipe.scheduler.config, shift=5.0)
    boundary = pipe.config.boundary_ratio * pipe.scheduler.config.num_train_timesteps

    def load_expert(noise: str):
        """One expert with its LoRAs, as pipe.transformer, where load_lora_weights puts them."""
        path = hf_hub_download(GGUF_REPO, f"{noise}/Wan2.2-I2V-A14B-{noise}-{quant}.gguf")
        model = WanTransformer3DModel.from_single_file(
            path, quantization_config=GGUFQuantizationConfig(compute_dtype=dtype),
            config=BASE_REPO, subfolder="transformer" if noise == "HighNoise" else "transformer_2", dtype=dtype,
        )
        pipe.register_modules(transformer=model)
        names, weights = [], []
        if lightning:
            part = "high_noise_model" if noise == "HighNoise" else "low_noise_model"
            pipe.load_lora_weights(LIGHTNING_REPO, weight_name=f"{LIGHTNING_DIR}/{part}.safetensors", adapter_name="lightning")
            names.append("lightning")
            weights.append(1.0)
        if pixel_strength > 0:
            # The LoRA's own workflow puts the same file on both experts.
            repo, weight = PIXEL_LORA
            pipe.load_lora_weights(repo, weight_name=weight, adapter_name="pixel")
            names.append("pixel")
            weights.append(pixel_strength)
        if names:
            model.set_adapters(names, weights)

        return model.to(device)

    def denoise(model, latents, condition, prompt: str, high: bool):
        """The steps of one expert: the high-noise one above the boundary, the low-noise one below it."""
        positive, negative = embeds[prompt]
        positive = positive.to(device)
        negative = None if negative is None else negative.to(device)
        latents, condition = latents.to(device), condition.to(device)

        pipe.scheduler.set_timesteps(steps, device=device)
        for t in pipe.scheduler.timesteps:
            if (t >= boundary) != high:
                continue
            hidden = torch.cat([latents, condition], dim=1).to(dtype)
            timestep = t.expand(latents.shape[0])
            noise = model(hidden_states=hidden, timestep=timestep, encoder_hidden_states=positive, return_dict=False)[0]
            if negative is not None:
                unconditional = model(hidden_states=hidden, timestep=timestep, encoder_hidden_states=negative,
                                      return_dict=False)[0]
                noise = unconditional + guidance * (noise - unconditional)
            latents = pipe.scheduler.step(noise, t, latents, return_dict=False)[0]

        return latents.cpu()

    def decode(latents) -> list[Image.Image]:
        latents = latents.to(device, pipe.vae.dtype)
        mean = torch.tensor(pipe.vae.config.latents_mean).view(1, -1, 1, 1, 1).to(latents)
        std = torch.tensor(pipe.vae.config.latents_std).view(1, -1, 1, 1, 1).to(latents)
        video = pipe.vae.decode(latents * std + mean, return_dict=False)[0]

        return pipe.video_processor.postprocess_video(video, output_type="pil")[0]

    def pixels_of(image: Image.Image):
        return pipe.video_processor.preprocess(image, height=size, width=size).to(device, dtype=torch.float32)

    def animate_all(inputs: list[tuple[str, Image.Image, int, Image.Image | None]]) -> Iterator[list[Image.Image]]:
        with torch.no_grad():
            started = []
            for prompt, image, seed, last in inputs:
                # With a last picture, the condition holds the first and the last frame, and the mask
                # marks both as given: the model fills the frames between.
                latents, condition = pipe.prepare_latents(
                    pixels_of(image), 1, pipe.vae.config.z_dim, size, size, frames, torch.float32, device,
                    torch.Generator("cpu").manual_seed(seed), None, None if last is None else pixels_of(last),
                )
                started.append((prompt, latents.cpu(), condition.cpu()))

            clock = time.monotonic()
            log("Loading the high-noise expert...")
            model = load_expert("HighNoise")
            log(f"  loaded in {time.monotonic() - clock:.0f}s")
            halfway = []
            for index, (prompt, latents, condition) in enumerate(started):
                clock = time.monotonic()
                halfway.append((prompt, denoise(model, latents, condition, prompt, high=True), condition))
                log(f"  high-noise {index + 1}/{len(started)}: {time.monotonic() - clock:.0f}s")
            pipe.register_modules(transformer=None)
            del model
            free_memory()

            clock = time.monotonic()
            log("Loading the low-noise expert...")
            model = load_expert("LowNoise")
            log(f"  loaded in {time.monotonic() - clock:.0f}s")
            for index, (prompt, latents, condition) in enumerate(halfway):
                clock = time.monotonic()
                video = decode(denoise(model, latents, condition, prompt, high=False))
                log(f"  low-noise and decode {index + 1}/{len(halfway)}: {time.monotonic() - clock:.0f}s")
                free_memory()
                yield video

    return animate_all
