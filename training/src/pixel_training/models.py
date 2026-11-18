from dataclasses import dataclass
from typing import Callable

from PIL import Image

Generate = Callable[[str, Image.Image | None, int], Image.Image]


@dataclass(frozen=True)
class Preset:
    name: str
    repo: str
    family: str
    steps: int
    guidance: float | None
    license: str


PRESETS = {
    "flux3-klein": Preset(
        "flux3-klein", "black-forest-labs/flux-3-image-klein", "flux3", 16, None,
        "FLUX Kommunity License: selling a fine-tuned version needs BFL's separate licence",
    ),
    "flux2-klein-4b": Preset(
        "flux2-klein-4b", "black-forest-labs/FLUX.2-klein-4B", "flux2", 4, 1.0,
        "Apache-2.0",
    ),
}


def pick_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"

    return "cuda" if torch.cuda.is_available() else "cpu"


def load_flux3(preset: Preset, device: str):
    import torch
    from diffusers import Flux3DistilledAutoBlocks

    blocks = Flux3DistilledAutoBlocks()
    # The upsampler rewrites the prompt into a long caption with a model of its own; we want
    # our words used as written, and the memory it would take on a 32 GB Mac.
    blocks.sub_blocks.pop("prompt_upsampler")

    pipe = blocks.init_pipeline(preset.repo)
    pipe.load_components(torch_dtype=torch.bfloat16)

    return pipe.to(device)


def load_flux2(preset: Preset, device: str):
    import torch
    from diffusers import Flux2KleinPipeline

    return Flux2KleinPipeline.from_pretrained(preset.repo, torch_dtype=torch.bfloat16).to(device)


def generator_for(preset: Preset, device: str, size: int) -> Generate:
    import torch

    pipe = load_flux3(preset, device) if preset.family == "flux3" else load_flux2(preset, device)
    extra = {} if preset.guidance is None else {"guidance_scale": preset.guidance}

    def generate(prompt: str, image: Image.Image | None, seed: int) -> Image.Image:
        inputs = {"prompt": prompt, "height": size, "width": size, "num_inference_steps": preset.steps, **extra}
        inputs["generator"] = torch.Generator("cpu").manual_seed(seed)

        if image is not None:
            inputs["image"] = image

        if preset.family == "flux3":
            return pipe(**inputs, output="images")[0]

        return pipe(**inputs).images[0]

    return generate


def free_memory() -> None:
    import gc

    import torch

    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()
