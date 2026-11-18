import argparse
import json
from datetime import datetime
from pathlib import Path

from pixel_training.models import PRESETS
from pixel_training.tryout import GENERATE_SIZE, Plan, create_jobs, rotate_jobs, run_model, write_results

ACCESS_HINT = (
    "  Log in once with `uv run hf auth login`, and accept the model's licence on its Hugging Face page "
    "with the same account."
)


def loader(name: str, device: str):
    from pixel_training.models import generator_for

    return lambda: generator_for(PRESETS[name], device, GENERATE_SIZE)


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
    plan = Plan(
        folder=args.data / "tryouts" / name,
        create=create_jobs(prompts),
        rotate=rotate_jobs(args.data / "exports" / args.export, prompts, args.rotate),
        seeds=list(range(args.seeds)),
    )
    device = pick_device()

    print(f"{len(plan.create)} prompts x {len(plan.seeds)} seeds, {len(plan.rotate)} rotations, on {device}")
    models = {}
    for model in args.models:
        print(f"== {model} ({PRESETS[model].license})")
        models[model] = run_model(plan, model, loader(model, device))
        report(model, models[model])

        # Written after every model, so a crash in the next one keeps what is done.
        write_results(plan, name, {**models, **{key: {"pending": True} for key in args.models if key not in models}},
                      {"device": device, "repos": {key: PRESETS[key].repo for key in args.models}})
        free_memory()

    print(f"\nResults in {plan.folder}. Open them with `uv run pixel browse` in dataset/, under Try-outs.")


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

    return root


def main() -> None:
    args = parser().parse_args()

    if args.command == "tryout":
        tryout_command(args)
