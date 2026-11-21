"""A character sprite to a short animation: Wan 2.2 image-to-video with the pixel-animate LoRA.

Wan 2.2 I2V A14B has two experts of 14B each: the high-noise one lays out the motion in the first
steps, the low-noise one draws the detail in the last steps. At full size they take about 56 GB, so
on a 32 GB Mac they are loaded as 4-bit GGUF files (about 10 GB each). The setup follows the
pixel-animate LoRA's own ComfyUI workflow: the LoRA on both experts, a 4-step speed-up LoRA
(lightx2v Lightning) on both, guidance 1, shift 5, two steps per expert.

A video model does not keep the pixel grid, so every frame is snapped back to a sprite with the
colours of the input sprite, and a few evenly spaced frames make the sprite sheet.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from PIL import Image

from pixel_training.pixelate import block_mode, blow_up, clear_background, palette_of

BASE_REPO = "Wan-AI/Wan2.2-I2V-A14B-Diffusers"
GGUF_REPO = "QuantStack/Wan2.2-I2V-A14B-GGUF"
PIXEL_LORA = ("styly-agents/Wan2-2-pixel-animate", "wan2.2_animate_adapter_model.safetensors")
LIGHTNING_REPO = "lightx2v/Wan2.2-Lightning"
LIGHTNING_DIR = "Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1"

SPRITE = 64
SHEET_SCALE = 4
FPS = 16

# What each action asks for. The subject comes from the generated character's prompt.
ACTIONS = {
    "idle": "idle animation, standing in place and breathing, small up and down motion, loops",
    "walk": "walking cycle in place, legs and arms swing, the character does not move across the frame, loops",
    "attack": "attack animation, swings the weapon forward and returns to the start pose",
}
VIEW_WORDS = {"front": "facing the viewer", "left": "facing left, side view", "back": "seen from the back",
              "right": "facing right, side view"}
TEMPLATE = ("pixel art game sprite animation of {subject}, {view}, {action}. Crisp pixel art, the same character "
            "in every frame, plain flat white background, the camera does not move")

# The pipeline's list of frames for one prompt, picture and seed.
Animate = Callable[[str, Image.Image, int], list[Image.Image]]


@dataclass(frozen=True)
class Job:
    id: str
    sprite: Path
    prompt: str
    seed: int


def jobs_for(source: Path, seeds: list[int], views: list[str], actions: list[str]) -> list[Job]:
    """One job per seed, view and action, from the sprites `pixel-train generate` wrote."""
    subject = json.loads((source / "generated.json").read_text())["prompt"]
    jobs = []
    for seed in seeds:
        for view in views:
            sprite = source / f"s{seed}-{view}.png"
            if not sprite.exists():
                continue
            for action in actions:
                prompt = TEMPLATE.format(subject=subject, view=VIEW_WORDS[view], action=ACTIONS[action])
                jobs.append(Job(f"s{seed}-{view}-{action}", sprite, prompt, seed))

    return jobs


def pick(frames: list, count: int) -> list:
    """`count` evenly spaced frames, without the first one: that is the input picture itself."""
    rest = frames[1:] or frames
    if count >= len(rest):
        return list(rest)

    return [rest[round(index * len(rest) / count)] for index in range(count)]


def snap(frame: Image.Image, palette: Image.Image) -> Image.Image:
    """A video frame back to a 64x64 sprite in the input sprite's colours, so frames do not flicker."""
    return clear_background(block_mode(frame, SPRITE, palette))


def save_gif(sprites: list[Image.Image], path: Path, fps: int) -> None:
    size = SPRITE * SHEET_SCALE
    frames = []
    for sprite in sprites:
        flat = Image.new("RGBA", sprite.size, (255, 255, 255, 255))
        flat.alpha_composite(sprite.convert("RGBA"))
        frames.append(flat.convert("RGB").resize((size, size), Image.NEAREST))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=round(1000 / fps), loop=0)


def save_strip(sprites: list[Image.Image], path: Path) -> None:
    size = SPRITE * SHEET_SCALE
    strip = Image.new("RGBA", (size * len(sprites), size), (255, 255, 255, 255))
    for index, sprite in enumerate(sprites):
        strip.alpha_composite(sprite.convert("RGBA").resize((size, size), Image.NEAREST), (index * size, 0))
    strip.save(path)


def run(folder: Path, jobs: list[Job], animate: Animate, size: int, keep: int, fps: int = FPS) -> list[dict]:
    """Animate every job; keep the raw video as a GIF, the snapped frames, and the sheet of `keep` frames."""
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for job in jobs:
        source = Image.open(job.sprite)
        frames = animate(job.prompt, blow_up(source, size), job.seed)

        small = [frame.convert("RGB").resize((256, 256), Image.LANCZOS) for frame in frames]
        small[0].save(folder / f"{job.id}-raw.gif", save_all=True, append_images=small[1:],
                      duration=round(1000 / fps), loop=0)

        palette = palette_of(source)
        sprites = [snap(frame, palette) for frame in frames]
        save_gif(sprites, folder / f"{job.id}.gif", fps)

        chosen = pick(sprites, keep)
        save_strip(chosen, folder / f"{job.id}-sheet.png")
        rows.append({"id": job.id, "sprite": str(job.sprite), "prompt": job.prompt, "seed": job.seed,
                     "frames": len(frames), "kept": len(chosen)})

    return rows


def write_info(folder: Path, info: dict) -> None:
    info = {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **info}
    (folder / "animated.json").write_text(json.dumps(info, indent=2))


def wan_animator(prompts: list[str], device: str, size: int, frames: int, steps: int, quant: str,
                 lightning: bool, pixel_strength: float) -> Animate:
    """Load Wan 2.2 I2V A14B in pieces, so the text encoder and the two experts are never in memory together."""
    import torch
    from diffusers import FlowMatchEulerDiscreteScheduler, GGUFQuantizationConfig, WanImageToVideoPipeline, WanTransformer3DModel
    from huggingface_hub import hf_hub_download

    from pixel_training.models import free_memory

    dtype = torch.bfloat16
    pipe = WanImageToVideoPipeline.from_pretrained(BASE_REPO, transformer=None, transformer_2=None, torch_dtype=dtype)

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
    pipe.text_encoder = None
    pipe.register_modules(text_encoder=None)
    free_memory()

    def expert(noise: str, subfolder: str):
        path = hf_hub_download(GGUF_REPO, f"{noise}/Wan2.2-I2V-A14B-{noise}-{quant}.gguf")
        return WanTransformer3DModel.from_single_file(
            path, quantization_config=GGUFQuantizationConfig(compute_dtype=dtype),
            config=BASE_REPO, subfolder=subfolder, torch_dtype=dtype,
        )

    pipe.register_modules(transformer=expert("HighNoise", "transformer"), transformer_2=expert("LowNoise", "transformer_2"))

    names, weights = [], []
    if lightning:
        pipe.load_lora_weights(LIGHTNING_REPO, weight_name=f"{LIGHTNING_DIR}/high_noise_model.safetensors", adapter_name="lightning")
        pipe.load_lora_weights(LIGHTNING_REPO, weight_name=f"{LIGHTNING_DIR}/low_noise_model.safetensors",
                               adapter_name="lightning", load_into_transformer_2=True)
        names.append("lightning")
        weights.append(1.0)
    if pixel_strength > 0:
        # The LoRA's own workflow puts it on both experts.
        repo, weight = PIXEL_LORA
        pipe.load_lora_weights(repo, weight_name=weight, adapter_name="pixel")
        pipe.load_lora_weights(repo, weight_name=weight, adapter_name="pixel", load_into_transformer_2=True)
        names.append("pixel")
        weights.append(pixel_strength)
    if names:
        pipe.transformer.set_adapters(names, weights)
        pipe.transformer_2.set_adapters(names, weights)

    pipe.scheduler = FlowMatchEulerDiscreteScheduler.from_config(pipe.scheduler.config, shift=5.0)
    pipe.to(device)

    def animate(prompt: str, image: Image.Image, seed: int) -> list[Image.Image]:
        positive, negative = embeds[prompt]
        with torch.no_grad():
            out = pipe(
                image=image, prompt_embeds=positive.to(device),
                negative_prompt_embeds=None if negative is None else negative.to(device),
                height=size, width=size, num_frames=frames, num_inference_steps=steps,
                guidance_scale=guidance, guidance_scale_2=guidance,
                generator=torch.Generator("cpu").manual_seed(seed), output_type="pil",
            )
        free_memory()

        return out.frames[0]

    return animate
