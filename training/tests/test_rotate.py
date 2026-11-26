import json
import sys
from pathlib import Path

import pytest
from PIL import Image

from pixel_training import cli, models

PROMPTS = Path(__file__).parents[1] / "prompts.json"


def fake(calls: list):
    def generate(prompt, image, seed):
        calls.append((prompt[:20], image.size, seed))
        return Image.new("RGB", image.size, (200, 30, 30))

    return generate


@pytest.fixture
def data(tmp_path, monkeypatch):
    calls = []
    loads = []
    monkeypatch.setattr(models, "pick_device", lambda: "cpu")
    monkeypatch.setattr(models, "generator_for", lambda *given: loads.append(given[2:4]) or fake(calls))

    for name, task in (("rotate-v2", "rotate"), ("create-v1", "create")):
        (tmp_path / "runs" / name / "final").mkdir(parents=True)
        (tmp_path / "runs" / name / "run.json").write_text(json.dumps({"settings": {"task": task, "size": 256}}))

    knight = tmp_path / "generated" / "knight"
    knight.mkdir(parents=True)
    (knight / "generated.json").write_text(json.dumps({"prompt": "a knight"}))
    for name in ("s0-front", "s0-front-raw", "s2-front", "s2-front-raw", "s2-left"):
        Image.new("RGBA", (64, 64), (30, 30, 200, 255)).save(knight / f"{name}.png")

    return tmp_path, calls, loads


def rotate(monkeypatch, data_folder, *words):
    argv = ["pixel-train", "--data", str(data_folder), "rotate", *words, "--prompts", str(PROMPTS)]
    monkeypatch.setattr(sys, "argv", argv)
    cli.main()


def test_a_generated_character_is_turned_into_a_new_folder(data, monkeypatch):
    folder, calls, loads = data

    rotate(monkeypatch, folder, "knight", "--lora", "rotate-v2", "--seeds", "2", "--name", "turned")

    turned = folder / "generated" / "turned"
    names = sorted(path.name for path in turned.iterdir())
    assert names == ["generated.json", "s2-back-raw.png", "s2-back.png", "s2-front-raw.png", "s2-front.png",
                     "s2-left-raw.png", "s2-left.png", "s2-right-raw.png", "s2-right.png", "s2-sheet.png"]
    assert [(size, seed) for _, size, seed in calls] == [((512, 512), 2)] * 3
    assert loads == [(512, folder / "runs" / "rotate-v2" / "final")]
    assert Image.open(turned / "s2-sheet.png").size == (4 * 256, 256)
    info = json.loads((turned / "generated.json").read_text())
    assert (info["prompt"], info["seeds"], info["views"]) == ("a knight", [2], ["left", "back", "right"])
    assert info["rotated_from"] == str(folder / "generated" / "knight")


def test_every_front_is_turned_by_default_and_views_can_be_chosen(data, monkeypatch):
    folder, calls, _ = data

    rotate(monkeypatch, folder, "knight", "--lora", "rotate-v2", "--views", "back", "--sprite", "64", "--name", "back")

    assert [(size, seed) for _, size, seed in calls] == [((256, 256), 0), ((256, 256), 2)]
    assert Image.open(folder / "generated" / "back" / "s0-sheet.png").size == (2 * 256, 256)
    assert not (folder / "generated" / "back" / "s0-left.png").exists()


def test_a_big_png_is_snapped_to_the_sprite_and_turned(data, monkeypatch):
    folder, calls, _ = data
    picture = folder / "uploads" / "hero.png"
    picture.parent.mkdir()
    Image.new("RGB", (300, 200), (255, 255, 255)).save(picture)

    rotate(monkeypatch, folder, str(picture), "--lora", "rotate-v2", "--sprite", "64", "--name", "hero")

    turned = folder / "generated" / "hero"
    assert Image.open(turned / "s0-front.png").size == (64, 64)
    assert Image.open(turned / "s0-front-raw.png").size == (300, 300)
    assert len(calls) == 3
    assert json.loads((turned / "generated.json").read_text())["prompt"] == "hero"


def test_a_small_png_is_kept_as_drawn(data, monkeypatch):
    folder, _, _ = data
    picture = folder / "slime.png"
    Image.new("RGBA", (32, 32), (30, 200, 30, 255)).save(picture)

    rotate(monkeypatch, folder, str(picture), "--lora", "rotate-v2", "--name", "slime")

    assert Image.open(folder / "generated" / "slime" / "s0-front.png").size == (32, 32)
    assert Image.open(folder / "generated" / "slime" / "s0-back.png").size == (128, 128)


@pytest.mark.parametrize(("words", "message"), [
    (["knight", "--lora", "create-v1"], "needs a rotate LoRA"),
    (["knight", "--lora", "rotate-v2", "--seeds", "5"], "no front view for seeds"),
    (["nobody", "--lora", "rotate-v2"], "No character at"),
    (["knight", "--lora", "rotate-v2", "--name", "knight"], "is already there"),
])
def test_a_bad_source_stops_before_any_model_loads(data, monkeypatch, words, message):
    folder, calls, loads = data

    with pytest.raises(SystemExit, match=message):
        rotate(monkeypatch, folder, *words)

    assert calls == loads == []
    assert sorted(path.name for path in (folder / "generated").iterdir()) == ["knight"]


def test_rotate_needs_a_lora():
    with pytest.raises(SystemExit):
        cli.parser().parse_args(["rotate", "knight"])
