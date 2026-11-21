"""FLUX.2 Klein with a LoRA, trained to turn a front view into another view.

A LoRA is a small set of extra weights next to the frozen model. Only those are trained, so it
fits on a 32 GB Mac and the file it writes is tens of MB, not GB.

One training example is: the front view as the reference image (as in an edit), the instruction
for the view from prompts.json, and the real view as the picture to make. The loss is flow
matching, the way FLUX is trained: mix the real view's latents with noise at a random level, and
ask the model for the direction from the picture to the noise.
"""

import math
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from pixel_training.models import Preset
from pixel_training.pixelate import blow_up
from pixel_training.train import Pair

# Every attention and projection layer, in the double blocks and in the single blocks. In the
# double blocks `to_out` is a list, so its first item is named; in the single blocks it is a layer.
TARGETS = (r".*(attn\.(to_q|to_k|to_v|to_out\.0|add_q_proj|add_k_proj|add_v_proj|to_add_out|to_qkv_mlp_proj)"
           r"|single_transformer_blocks\.\d+\.attn\.to_out)$")
LORA_FILE = "pytorch_lora_weights.safetensors"
VAL_SEED = 1234


def picture(path: Path, size: int) -> torch.Tensor:
    """A sprite scaled up on white, as the try-out shows it to the model, in [-1, 1]."""
    array = np.asarray(blow_up(Image.open(path), size), dtype=np.float32)

    return torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0) / 127.5 - 1


def shift(sigmas: torch.Tensor, mu: float) -> torch.Tensor:
    # The same time shift the scheduler applies when it samples, so training spends its steps on
    # the noise levels the model sees when it makes a picture.
    return math.exp(mu) / (math.exp(mu) + (1 / sigmas - 1))


class FluxLora:
    def __init__(self, preset: Preset, device: str, size: int, rank: int, learning_rate: float,
                 instructions: dict[str, str], seed: int):
        from diffusers import AutoencoderKLFlux2, Flux2KleinPipeline, Flux2Transformer2DModel
        from diffusers.pipelines.flux2.pipeline_flux2_klein import compute_empirical_mu
        from peft import LoraConfig
        from transformers import Qwen2TokenizerFast, Qwen3ForCausalLM

        self.device, self.size, self.preset = device, size, preset
        self.pipeline = Flux2KleinPipeline
        dtype = torch.bfloat16

        # There are only a few instructions, so they are turned into embeddings once and the text
        # model (8 GB) is let go before training starts.
        tokenizer = Qwen2TokenizerFast.from_pretrained(preset.parts, subfolder="tokenizer")
        text_encoder = Qwen3ForCausalLM.from_pretrained(preset.parts, subfolder="text_encoder", dtype=dtype).to(device)
        self.prompts = {}
        with torch.no_grad():
            for view, instruction in instructions.items():
                embeds = Flux2KleinPipeline._get_qwen3_prompt_embeds(text_encoder, tokenizer, instruction, dtype, device)
                self.prompts[view] = (embeds, Flux2KleinPipeline._prepare_text_ids(embeds).to(device))
        del text_encoder
        free(device)

        self.vae = AutoencoderKLFlux2.from_pretrained(preset.parts, subfolder="vae", dtype=dtype).to(device)
        self.vae.requires_grad_(False)
        self.transformer = Flux2Transformer2DModel.from_pretrained(preset.repo, subfolder="transformer", dtype=dtype)
        self.transformer.requires_grad_(False)
        self.transformer.enable_gradient_checkpointing()
        self.transformer.add_adapter(LoraConfig(r=rank, lora_alpha=rank, init_lora_weights="gaussian", target_modules=TARGETS))
        self.transformer.to(device)

        # The LoRA weights train in float32: in bfloat16 small updates round away.
        self.weights = [weight for weight in self.transformer.parameters() if weight.requires_grad]
        for weight in self.weights:
            weight.data = weight.data.float()
        self.optimizer = torch.optim.AdamW(self.weights, lr=learning_rate, weight_decay=1e-4)

        tokens = (size // 16) ** 2
        self.mu = compute_empirical_mu(image_seq_len=tokens, num_steps=preset.steps)
        self.generator = torch.Generator("cpu").manual_seed(seed)
        self.latents = {}

    def encode(self, path: Path, keep: bool) -> torch.Tensor:
        """A picture to patched, normalised latents (1, 128, size/16, size/16), as the pipeline makes them."""
        if path in self.latents:
            return self.latents[path].to(self.device)

        with torch.no_grad():
            image = picture(path, self.size).to(self.device, self.vae.dtype)
            latents = self.pipeline._patchify_latents(self.vae.encode(image).latent_dist.mode()).float()
            mean = self.vae.bn.running_mean.view(1, -1, 1, 1).to(latents)
            std = torch.sqrt(self.vae.bn.running_var.view(1, -1, 1, 1) + self.vae.config.batch_norm_eps).to(latents)
            latents = (latents - mean) / std

        # Only the fixed check pairs are kept: they come back at every checkpoint, while a training
        # pair rarely comes back, and keeping them all would take tens of GB.
        if keep:
            self.latents[path] = latents.cpu()

        return latents

    def loss(self, pair: Pair, generator: torch.Generator, keep: bool = False) -> torch.Tensor:
        target = self.encode(pair.target, keep)
        reference = self.encode(pair.front, keep)
        embeds, text_ids = self.prompts[pair.view]

        noise = torch.randn(target.shape, generator=generator).to(self.device)
        sigma = shift(torch.sigmoid(torch.randn(1, generator=generator)), self.mu).to(self.device)
        noisy = (1 - sigma) * target + sigma * noise

        pack = self.pipeline._pack_latents
        image_ids = self.pipeline._prepare_latent_ids(target).to(self.device)
        reference_ids = self.pipeline._prepare_image_ids([reference]).to(self.device)

        prediction = self.transformer(
            hidden_states=torch.cat([pack(noisy), pack(reference)], dim=1).to(torch.bfloat16),
            encoder_hidden_states=embeds,
            timestep=sigma.to(torch.bfloat16),
            img_ids=torch.cat([image_ids, reference_ids], dim=1),
            txt_ids=text_ids,
            guidance=None,
            return_dict=False,
        )[0]
        prediction = prediction[:, : pack(target).shape[1]]

        return torch.nn.functional.mse_loss(prediction.float(), pack(noise - target).float())

    def train_step(self, pairs: list[Pair]) -> float:
        self.transformer.train()
        total = 0.0
        for pair in pairs:
            loss = self.loss(pair, self.generator) / len(pairs)
            loss.backward()
            total += loss.item()

        torch.nn.utils.clip_grad_norm_(self.weights, 1.0)
        self.optimizer.step()
        self.optimizer.zero_grad(set_to_none=True)

        return total

    def val_loss(self, pairs: list[Pair]) -> float:
        self.transformer.eval()
        generator = torch.Generator("cpu").manual_seed(VAL_SEED)
        with torch.no_grad():
            losses = [self.loss(pair, generator, keep=True).item() for pair in pairs]

        return sum(losses) / max(1, len(losses))

    def save(self, folder: Path) -> None:
        from peft.utils import get_peft_model_state_dict

        layers = {name: weight.to(torch.bfloat16) for name, weight in get_peft_model_state_dict(self.transformer).items()}
        self.pipeline.save_lora_weights(folder, transformer_lora_layers=layers)
        torch.save({"optimizer": self.optimizer.state_dict(), "generator": self.generator.get_state()}, folder / "optimizer.pt")

    def load(self, folder: Path) -> None:
        from peft.utils import set_peft_model_state_dict
        from safetensors.torch import load_file

        saved = load_file(folder / LORA_FILE)
        layers = {name.removeprefix("transformer."): weight.float() for name, weight in saved.items()}
        set_peft_model_state_dict(self.transformer, layers)

        state = torch.load(folder / "optimizer.pt", weights_only=False)
        self.optimizer.load_state_dict(state["optimizer"])
        self.generator.set_state(state["generator"])


def free(device: str) -> None:
    import gc

    gc.collect()
    if device == "mps":
        torch.mps.empty_cache()
    elif device == "cuda":
        torch.cuda.empty_cache()
