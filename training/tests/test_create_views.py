import json
from pathlib import Path

from pixel_training.cli import create_views, parser
from pixel_training.train import SIDE, Captions, Pair, read_captioned

TEMPLATE = "sprite of {subject}, {view}"


def captioned_export(folder: Path, views: tuple[str, ...]) -> Path:
    row = {"character": "lpc/a", "source": "lpc", "split": "train", "caption": "a knight",
           "views": {view: f"images/a/{view}.png" for view in views}}
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "characters.jsonl").write_text(json.dumps(row))

    return folder


def test_a_create_run_learns_the_side_from_the_right_view(tmp_path):
    export = captioned_export(tmp_path, ("front", "left", "back", "right"))

    found = read_captioned(export, "train", Captions(TEMPLATE, views=("front", "side")))

    assert found == [
        Pair("lpc/a", "front", None, export / "images/a/front.png", "sprite of a knight, front view facing the viewer"),
        Pair("lpc/a", "side", None, export / "images/a/right.png", f"sprite of a knight, {SIDE}"),
    ]


def test_a_character_with_no_right_view_gives_its_front_only(tmp_path):
    export = captioned_export(tmp_path, ("front",))

    found = read_captioned(export, "train", Captions(TEMPLATE, views=("front", "side")))

    assert [pair.view for pair in found] == ["front"]


def test_a_new_create_run_learns_front_and_side_views(tmp_path):
    args = parser().parse_args(["--data", str(tmp_path), "train", "--task", "create", "--name", "new"])

    assert create_views(args) == ("front", "side")


def test_a_run_that_goes_on_keeps_its_views(tmp_path):
    for name, settings in (("old", {"task": "create"}), ("both", {"task": "create", "views": ["front", "side"]})):
        (tmp_path / "runs" / name).mkdir(parents=True)
        (tmp_path / "runs" / name / "run.json").write_text(json.dumps({"settings": settings}))

    def views_of(name: str) -> tuple[str, ...]:
        return create_views(parser().parse_args(["--data", str(tmp_path), "train", "--name", name, "--views", "side"]))

    assert views_of("old") == ("front",)
    assert views_of("both") == ("front", "side")
