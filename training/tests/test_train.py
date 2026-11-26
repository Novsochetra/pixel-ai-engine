import json
from pathlib import Path

import pytest

from pixel_training.cli import parser
from pixel_training.train import (Pair, Settings, caption_text, latest_checkpoint, lora_folder, read_captioned,
                                  read_labels, read_pairs, repeated, run_settings, source_of, train,
                                  val_sample)

VIEWS = ["left", "back", "right"]


def fake_export(folder: Path) -> Path:
    rows = [("pac", "train", "a"), ("lpc", "train", "b"), ("pac", "val", "c"), ("pac", "test", "d")]
    lines = [json.dumps({"character": f"{source}/{name}", "source": source, "split": split,
                         "views": {view: f"images/{name}/{view}.png" for view in ("front", *VIEWS)}})
             for source, split, name in rows]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "characters.jsonl").write_text("\n".join(lines))

    return folder


class FakeBackend:
    """Remembers what it was asked; its loss goes down by one every step."""

    def __init__(self):
        self.seen, self.loaded, self.loss = [], None, 100.0

    def train_step(self, pairs):
        self.seen.append([pair.character + "/" + pair.view for pair in pairs])
        self.loss -= 1
        return self.loss

    def val_loss(self, pairs):
        return self.loss / 2

    def save(self, folder):
        (folder / "pytorch_lora_weights.safetensors").write_text(str(self.loss))

    def load(self, folder):
        self.loaded = folder.name
        self.loss = float((folder / "pytorch_lora_weights.safetensors").read_text())


def settings(steps=5, every=2) -> Settings:
    return Settings(model="fake", export="x", size=64, steps=steps, rank=4, learning_rate=1e-4, accumulate=2,
                    every=every, val_count=1, sources=(), seed=0)


def pairs(count=6) -> list[Pair]:
    return [Pair(f"c{index}", "left", Path("f.png"), Path("t.png")) for index in range(count)]


def test_pairs_are_one_per_character_and_view_of_the_split(tmp_path):
    found = read_pairs(fake_export(tmp_path), "train", VIEWS)

    assert {(pair.character, pair.view) for pair in found} == {(c, v) for c in ("pac/a", "lpc/b") for v in VIEWS}
    assert all(pair.front.name == "front.png" and pair.target.name == f"{pair.view}.png" for pair in found)


def test_pairs_can_be_limited_to_some_sources(tmp_path):
    found = read_pairs(fake_export(tmp_path), "train", VIEWS, sources=("lpc",))

    assert {pair.character for pair in found} == {"lpc/b"}


def test_the_check_pairs_are_the_same_every_time():
    assert val_sample(pairs(), 3, seed=1) == val_sample(pairs(), 3, seed=1)
    assert len(val_sample(pairs(2), 16, seed=1)) == 2


def test_a_run_saves_checkpoints_a_log_and_a_final_lora(tmp_path):
    run = tmp_path / "run"

    result = train(run, settings(), pairs(), pairs(1), FakeBackend(), say=lambda _: None)

    rows = [json.loads(line) for line in (run / "log.jsonl").read_text().splitlines()]
    assert [row["step"] for row in rows] == [1, 2, 3, 4, 5]
    assert [row["step"] for row in rows if "val_loss" in row] == [2, 4, 5]
    assert sorted(path.name for path in (run / "checkpoints").iterdir()) == ["step-000002", "step-000004", "step-000005"]
    assert (run / "final" / "pytorch_lora_weights.safetensors").is_file()
    assert result["val_loss"] == 47.5


def test_a_resumed_run_goes_on_where_it_stopped_and_sees_the_same_pairs(tmp_path):
    whole = FakeBackend()
    train(tmp_path / "whole", settings(steps=6), pairs(), pairs(1), whole, say=lambda _: None)

    first = FakeBackend()
    train(tmp_path / "broken", settings(steps=4), pairs(), pairs(1), first, say=lambda _: None)
    second = FakeBackend()
    train(tmp_path / "broken", settings(steps=6), pairs(), pairs(1), second, resume=True, say=lambda _: None)

    assert second.loaded == "step-000004"
    assert first.seen + second.seen == whole.seen
    assert second.loss == whole.loss


def test_a_new_run_does_not_write_over_an_old_one(tmp_path):
    train(tmp_path, settings(steps=1, every=1), pairs(), pairs(1), FakeBackend(), say=lambda _: None)

    with pytest.raises(FileExistsError):
        train(tmp_path, settings(steps=1, every=1), pairs(), pairs(1), FakeBackend(), say=lambda _: None)


def test_a_checkpoint_cut_off_halfway_is_not_picked_up(tmp_path):
    (tmp_path / "checkpoints" / "step-000004.partial").mkdir(parents=True)
    (tmp_path / "checkpoints" / "step-000002").mkdir()
    (tmp_path / "checkpoints" / "step-000002" / "state.json").write_text('{"step": 2}')

    assert latest_checkpoint(tmp_path) == (2, tmp_path / "checkpoints" / "step-000002")


def test_a_try_out_finds_the_lora_and_the_size_it_was_trained_at(tmp_path):
    run = tmp_path / "run"
    train(run, settings(steps=2, every=1), pairs(), pairs(1), FakeBackend(), say=lambda _: None)

    assert lora_folder(run) == run / "final"
    assert lora_folder(run / "checkpoints" / "step-000001") == run / "checkpoints" / "step-000001"
    assert run_settings(run / "checkpoints" / "step-000001")["size"] == 64


def test_train_defaults():
    args = parser().parse_args(["train"])

    assert (args.model, args.export, args.steps, args.size, args.rank, args.resume) == \
        ("flux2-klein-base-4b", "rotation-v1", 1000, 512, 16, False)


TEMPLATE = "pixel art game sprite of {subject}, front view"


def test_a_caption_is_put_in_the_words_generate_uses():
    caption = "lpc-style pixel art character, with male human body, tanned skin, wearing blue vest"

    assert caption_text(caption, TEMPLATE) == \
        "pixel art game sprite of a character with male human body, tanned skin, wearing blue vest, front view"


def test_create_pairs_are_the_captioned_front_views_of_the_split(tmp_path):
    export = fake_export(tmp_path)
    rows = [json.loads(line) for line in (export / "characters.jsonl").read_text().splitlines()]
    rows[1]["caption"] = "lpc-style pixel art character, with a hat"
    (export / "characters.jsonl").write_text("\n".join(json.dumps(row) for row in rows))

    found = read_captioned(export, "train", TEMPLATE)

    assert found == [Pair("lpc/b", "front", None, export / "images/b/front.png",
                          "pixel art game sprite of a character with a hat, front view")]


def test_a_create_run_remembers_its_task(tmp_path):
    run = tmp_path / "run"
    create = Settings(**{**settings(steps=1, every=1).__dict__, "task": "create"})

    train(run, create, [Pair("c", "front", None, Path("t.png"), "x")], [], FakeBackend(), say=lambda _: None)

    assert run_settings(run)["task"] == "create"
    assert parser().parse_args(["train"]).task == "rotate"


def test_a_character_without_a_caption_takes_its_ai_label(tmp_path):
    export = fake_export(tmp_path / "export")
    folder = tmp_path / "labels" / "pac"
    folder.mkdir(parents=True)
    (folder / "labels.jsonl").write_text(json.dumps({"character": "pac/a", "label": "a small chibi character with red hair."}))

    found = read_captioned(export, "train", TEMPLATE, labels=read_labels(tmp_path / "labels"))

    assert [(pair.character, pair.caption) for pair in found] == \
        [("pac/a", "pixel art game sprite of a small chibi character with red hair, front view")]


def test_a_skip_label_is_left_out(tmp_path):
    export = fake_export(tmp_path / "export")
    folder = tmp_path / "labels" / "pac"
    folder.mkdir(parents=True)
    (folder / "labels.jsonl").write_text(json.dumps({"character": "pac/a", "label": "skip"}))

    assert read_captioned(export, "train", TEMPLATE, labels=read_labels(tmp_path / "labels")) == []


def test_create_training_takes_more_exports():
    args = parser().parse_args(["train", "--task", "create", "--more-exports", "opengameart-v1"])

    assert args.more_exports == ["opengameart-v1"]
    assert args.more_repeat == 1
    assert parser().parse_args(["train"]).more_exports == []


def test_a_run_sees_every_pair_once_before_any_comes_back(tmp_path):
    backend = FakeBackend()
    train(tmp_path, settings(steps=6, every=10), pairs(6), pairs(1), backend, say=lambda _: None)

    first, second = sum(backend.seen[:3], []), sum(backend.seen[3:], [])
    assert sorted(first) == sorted(second) == sorted(f"c{index}/left" for index in range(6))
    assert first != second
    assert json.loads((tmp_path / "log.jsonl").read_text().splitlines()[2])["passes"] == 1.0


def test_a_source_can_be_shown_more_or_less_often():
    found = [Pair(f"{source}/{index}", "front", None, Path("t.png"))
             for source, count in (("lpc", 10), ("pixellab", 2)) for index in range(count)]

    kept = repeated(found, {"pixellab": 3, "lpc": 0.5}, seed=0)

    assert sum(source_of(pair) == "pixellab" for pair in kept) == 6
    assert sum(source_of(pair) == "lpc" for pair in kept) == 5
    assert kept == repeated(found, {"pixellab": 3, "lpc": 0.5}, seed=0)


def test_repeat_and_add_steps_are_read_from_the_command():
    args = parser().parse_args(["train", "--repeat", "pixellab=10", "lpc-4view=0.5", "--add-steps", "500"])

    assert args.repeat == [("pixellab", 10.0), ("lpc-4view", 0.5)]
    assert args.add_steps == 500
    with pytest.raises(SystemExit):
        parser().parse_args(["train", "--repeat", "pixellab"])
