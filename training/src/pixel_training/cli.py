import argparse
import json
from datetime import datetime
from pathlib import Path

from pixel_training.models import PRESETS
from pixel_training.train import lora_folder, run_settings
from pixel_training.tryout import GENERATE_SIZE, Plan, create_jobs, rotate_jobs, run_model, write_results

ACCESS_HINT = (
    "  Log in once with `uv run hf auth login`, and accept the model's licence on its Hugging Face page "
    "with the same account."
)


def loader(name: str, device: str, size: int, lora: Path | None, steps: int | None = None):
    from pixel_training.models import generator_for

    return lambda: generator_for(PRESETS[name], device, size, lora, steps)


def needs_login(error: str) -> bool:
    # A gated repository reached without a login reads as a missing config, not always as a 401.
    signs = ("401", "gated", "restricted", "failed to load config")

    return any(sign in error.lower() for sign in signs)


def report(name: str, result: dict) -> None:
    if "error" in result:
        print(f"  {name} failed: {result['error'][:400]}")
        if needs_login(result["error"]):
            print(ACCESS_HINT)
        return

    print(f"  {name}: loaded in {result['load_seconds']}s, {result['seconds_per_image']}s per image")


def tryout_command(args) -> None:
    from pixel_training.models import free_memory, pick_device

    prompts = json.loads(args.prompts.read_text())
    name = args.name or datetime.now().strftime("tryout-%Y%m%d-%H%M")
    lora = lora_folder(args.lora) if args.lora else None
    # A LoRA works best at the size it was trained at.
    size = args.size or (run_settings(lora).get("size", GENERATE_SIZE) if lora else GENERATE_SIZE)
    plan = Plan(
        folder=args.data / "tryouts" / name,
        create=[] if args.no_create else create_jobs(prompts),
        rotate=rotate_jobs(args.data / "exports" / args.export, prompts, args.rotate),
        seeds=list(range(args.seeds)),
        size=size,
    )
    device = pick_device()

    print(f"{len(plan.create)} prompts x {len(plan.seeds)} seeds, {len(plan.rotate)} rotations, {size}px, on {device}")
    if lora:
        print(f"with the LoRA in {lora}")
    if args.rotate and not plan.rotate:
        print(f"  No test characters to turn: run `uv run pixel export` in dataset/ first ({args.export}).")
    models = {}
    for model in args.models:
        print(f"== {model} ({PRESETS[model].license})")
        models[model] = run_model(plan, model, loader(model, device, size, lora, args.steps))
        report(model, models[model])

        # Written after every model, so a crash in the next one keeps what is done.
        write_results(plan, name, {**models, **{key: {"pending": True} for key in args.models if key not in models}},
                      {"device": device, "repos": {key: PRESETS[key].repo for key in args.models},
                       "lora": str(lora) if lora else None, "size": size, "steps": args.steps})
        free_memory()

    print(f"\nResults in {plan.folder}. Open them with `uv run pixel browse` in dataset/, under Try-outs.")


def train_command(args) -> None:
    from pixel_training.lora import FluxLora
    from pixel_training.models import pick_device
    from pixel_training.train import Settings, read_pairs, train, val_sample

    export = args.data / "exports" / args.export
    if not (export / "characters.jsonl").exists():
        raise SystemExit(f"No export at {export}. Run `uv run pixel export` in dataset/ first.")

    prompts = json.loads(args.prompts.read_text())["rotate"]
    sources = tuple(args.sources or ())
    train_pairs = read_pairs(export, "train", list(prompts), sources)
    val_pairs = val_sample(read_pairs(export, "val", list(prompts), sources), args.val, args.seed)
    if not train_pairs:
        raise SystemExit(f"No training pairs in {export} for sources {sources or 'all'}.")

    settings = Settings(model=args.model, export=args.export, size=args.size, steps=args.steps, rank=args.rank,
                        learning_rate=args.learning_rate, accumulate=args.accumulate, every=args.every,
                        val_count=len(val_pairs), sources=sources, seed=args.seed)
    run = args.data / "runs" / (args.name or datetime.now().strftime("lora-%Y%m%d-%H%M"))
    licences = json.loads((export / "export.json").read_text())["sources"]
    used = {name: info["license"] for name, info in licences.items() if not sources or name in sources}
    device = pick_device()

    print(f"{len(train_pairs):,} training pairs, {len(val_pairs)} check pairs, {args.size}px, on {device}")
    print(f"Sources and licences: {', '.join(f'{name} ({licence})' for name, licence in used.items())}")
    print(f"Run folder: {run}")
    print("Loading the model...")
    backend = FluxLora(PRESETS[args.model], device, args.size, args.rank, args.learning_rate, prompts, args.seed)

    result = train(run, settings, train_pairs, val_pairs, backend, resume=args.resume)
    print(f"\nDone. The LoRA is in {result['final']}.")
    print(f"Try it: uv run pixel-train tryout --models {args.model} --lora {run}")


def generate_command(args) -> None:
    from pixel_training.generate import make_fronts, sheets, turn, write_info
    from pixel_training.models import free_memory, generator_for, pick_device

    prompts = json.loads(args.prompts.read_text())
    text = args.prompt if args.raw else prompts["create"]["template"].format(subject=args.prompt)
    slug = "-".join("".join(c if c.isalnum() else " " for c in args.prompt.lower()).split())[:40]
    folder = args.data / "generated" / (args.name or f"{datetime.now():%Y%m%d-%H%M}-{slug}")
    seeds = list(range(args.seeds))
    device = pick_device()

    print(f"== front view: {args.front_model}, {args.front_size}px, {len(seeds)} seeds")
    front = generator_for(PRESETS[args.front_model], device, args.front_size)
    fronts = make_fronts(folder, text, seeds, front, args.sprite)
    del front
    free_memory()

    info = {"prompt": args.prompt, "text": text, "seeds": seeds, "front_model": args.front_model, "sprite": args.sprite}
    if args.lora:
        lora = lora_folder(args.lora)
        trained = run_settings(lora)
        model = args.turn_model or trained.get("model", "flux2-klein-base-4b")
        # The LoRA learnt on 64-pixel sprites, each pixel a block of size/64. A bigger sprite gets a
        # bigger picture, so its pixels are blocks of the same size.
        size = args.turn_size or trained.get("size", 512) * args.sprite // 64
        print(f"== turning with the LoRA in {lora}: {model}, {size}px")
        turner = generator_for(PRESETS[model], device, size, lora, args.steps)
        turn(folder, fronts, prompts["rotate"], turner, size, args.sprite)
        info |= {"lora": str(lora), "turn_model": model, "size": size}

    made = sheets(folder, seeds)
    write_info(folder, info)
    print(f"\nDone. Look at: {', '.join(str(path) for path in made)}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pixel-train", description="Try, train and evaluate pixel art models.")
    root.add_argument("--data", type=Path, default=Path("../dataset/data"), help="the dataset's data folder")
    commands = root.add_subparsers(dest="command", required=True)

    tryout = commands.add_parser("tryout", help="run existing models on test prompts and test characters, no training")
    tryout.add_argument("--models", nargs="+", choices=sorted(PRESETS), default=sorted(PRESETS))
    tryout.add_argument("--seeds", type=int, default=2, help="pictures per prompt")
    tryout.add_argument("--rotate", type=int, default=4, help="test characters to turn to left, back and right")
    tryout.add_argument("--export", default="rotation-v1", help="the export the test characters come from")
    tryout.add_argument("--prompts", type=Path, default=Path("prompts.json"))
    tryout.add_argument("--name", help="folder name under data/tryouts (default: tryout-<date>-<time>)")
    tryout.add_argument("--no-create", action="store_true", help="only the rotations, no text-to-character pictures")
    tryout.add_argument("--lora", type=Path, help="a training run folder (or one of its checkpoints) to try")
    tryout.add_argument("--size", type=int, help="picture size (default: the LoRA's training size, or 1024)")
    tryout.add_argument("--steps", type=int, help="sampling steps per picture (default: the model's own, 4 for FLUX.2 Klein)")

    train = commands.add_parser("train", help="train a LoRA that turns a front view into the left, back and right views")
    train.add_argument("--model", choices=["flux2-klein-base-4b", "flux2-klein-4b"], default="flux2-klein-base-4b",
                       help="the base model is made for training; the 4-step model trains blurry")
    train.add_argument("--export", default="rotation-v1", help="the export to train on")
    train.add_argument("--sources", nargs="+", help="train on these sources only (default: all in the export)")
    train.add_argument("--steps", type=int, default=1000, help="optimiser steps")
    train.add_argument("--accumulate", type=int, default=4, help="pairs per step")
    train.add_argument("--size", type=int, default=512, help="picture size the model sees, a multiple of 16")
    train.add_argument("--rank", type=int, default=16, help="LoRA size: higher learns more, and takes more memory")
    train.add_argument("--learning-rate", type=float, default=1e-4)
    train.add_argument("--every", type=int, default=100, help="check and save a checkpoint every this many steps")
    train.add_argument("--val", type=int, default=16, help="check pairs from the val split")
    train.add_argument("--seed", type=int, default=0)
    train.add_argument("--prompts", type=Path, default=Path("prompts.json"))
    train.add_argument("--name", help="folder name under data/runs (default: lora-<date>-<time>)")
    train.add_argument("--resume", action="store_true", help="go on from the last checkpoint of --name")

    flux2 = [name for name, preset in PRESETS.items() if preset.family == "flux2"]
    generate = commands.add_parser("generate", help="text to a character: the front view, and with --lora the left, back and right views")
    generate.add_argument("prompt", help="what to draw, for example \"a knight with a blue cape\"")
    generate.add_argument("--lora", type=Path, help="a training run (or checkpoint) that turns the front view to the other views")
    generate.add_argument("--seeds", type=int, default=2, help="characters to make, each from another seed")
    generate.add_argument("--front-model", choices=flux2, default="flux2-klein-4b", help="the model that draws the front view")
    generate.add_argument("--front-size", type=int, default=1024)
    generate.add_argument("--sprite", type=int, default=128,
                          help="sprite size in pixels: the model draws finer than 64, so 128 keeps faces and small parts")
    generate.add_argument("--turn-size", type=int, help="picture size for turning (default: the LoRA's training size, scaled with --sprite)")
    generate.add_argument("--turn-model", choices=flux2, help="the model that turns it (default: the one the LoRA was trained on)")
    generate.add_argument("--steps", type=int, help="sampling steps for turning (default: the model's own)")
    generate.add_argument("--raw", action="store_true", help="use the prompt as written, without the pixel art sprite wording")
    generate.add_argument("--prompts", type=Path, default=Path("prompts.json"))
    generate.add_argument("--name", help="folder name under data/generated (default: <date>-<prompt>)")

    return root


def main() -> None:
    args = parser().parse_args()

    if args.command == "tryout":
        tryout_command(args)
    elif args.command == "train":
        if args.resume and not args.name:
            raise SystemExit("--resume needs the --name of the run to go on with.")
        if args.size % 16:
            raise SystemExit("--size must be a multiple of 16.")
        train_command(args)
    elif args.command == "generate":
        generate_command(args)
