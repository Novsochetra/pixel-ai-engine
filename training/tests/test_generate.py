import json

from PIL import Image

from pixel_training.cli import parser
from pixel_training.generate import make_fronts, mirror, read_reference, sheets, turn, with_reference, write_info
from pixel_training.pixelate import Snap

INSTRUCTIONS = {"left": "turn left", "back": "turn around", "right": "turn right"}


def fake(calls: list):
    def generate(prompt, image, seed):
        calls.append((prompt, None if image is None else image.size, seed))
        return Image.new("RGB", (256, 256), (200, 30, 30))

    return generate


def test_text_to_front_views_one_per_seed(tmp_path):
    calls = []

    fronts = make_fronts(tmp_path, "a knight", [0, 1], fake(calls))

    assert [path.name for path in fronts] == ["s0-front.png", "s1-front.png"]
    assert calls == [("a knight", None, 0), ("a knight", None, 1)]
    assert Image.open(fronts[0]).size == (64, 64)
    assert (tmp_path / "s0-front-raw.png").is_file()


def test_each_front_is_turned_to_every_view_from_the_front_picture(tmp_path):
    fronts = make_fronts(tmp_path, "a knight", [0, 3], fake([]))
    calls = []

    turn(tmp_path, fronts, INSTRUCTIONS, fake(calls), 256)

    assert [(prompt, size, seed) for prompt, size, seed in calls] == \
        [(text, (256, 256), seed) for seed in (0, 3) for text in INSTRUCTIONS.values()]
    assert all((tmp_path / f"s3-{view}.png").is_file() for view in INSTRUCTIONS)


def test_a_sheet_shows_the_views_side_by_side(tmp_path):
    fronts = make_fronts(tmp_path, "a knight", [0], fake([]))
    turn(tmp_path, fronts, INSTRUCTIONS, fake([]), 256)

    sheet = Image.open(sheets(tmp_path, [0])[0])

    assert sheet.size == (4 * 256, 256)


def test_without_turning_the_sheet_has_the_front_only(tmp_path):
    make_fronts(tmp_path, "a knight", [0], fake([]))

    assert Image.open(sheets(tmp_path, [0])[0]).size == (256, 256)


def test_the_info_file_keeps_the_prompt(tmp_path):
    write_info(tmp_path, {"prompt": "a knight"})

    assert json.loads((tmp_path / "generated.json").read_text())["prompt"] == "a knight"


def test_generate_defaults():
    args = parser().parse_args(["generate", "a knight"])

    assert (args.prompt, args.seeds, args.front_model, args.lora, args.raw) == ("a knight", 2, "flux2-klein-4b", None, False)


def test_a_bigger_sprite_keeps_more_pixels(tmp_path):
    fronts = make_fronts(tmp_path, "a knight", [0], fake([]), Snap(128))
    turn(tmp_path, fronts, INSTRUCTIONS, fake([]), 256, Snap(128))

    assert Image.open(fronts[0]).size == (128, 128)
    assert Image.open(tmp_path / "s0-back.png").size == (128, 128)
    assert Image.open(sheets(tmp_path, [0])[0]).size == (4 * 256, 256)


def test_a_side_view_is_drawn_and_flipped_for_the_left(tmp_path):
    def half_red(prompt, image, seed):
        picture = Image.new("RGB", (256, 256), (255, 255, 255))
        picture.paste((200, 30, 30), (0, 0, 128, 256))
        return picture

    sides = make_fronts(tmp_path, "a dragon", [0], half_red, view="right")
    lefts = mirror(sides)

    assert [path.name for path in sides] == ["s0-right.png"]
    assert [path.name for path in lefts] == ["s0-left.png"]
    right, left = Image.open(sides[0]).convert("RGB"), Image.open(lefts[0]).convert("RGB")
    assert left.getpixel((0, 32)) == right.getpixel((63, 32))
    assert not (tmp_path / "s0-front.png").exists()
    assert Image.open(sheets(tmp_path, [0])[0]).size == (2 * 256, 256)


def test_a_reference_fills_the_empty_picture_slot_and_keeps_a_given_one():
    calls = []
    reference = Image.new("RGB", (32, 32))
    given = Image.new("RGB", (16, 16))

    draw = with_reference(fake(calls), reference)
    draw("a knight", None, 0)
    draw("turn left", given, 1)

    assert calls == [("a knight", (32, 32), 0), ("turn left", (16, 16), 1)]


def test_a_reference_is_scaled_up_with_hard_edges_on_white(tmp_path):
    sprite = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    sprite.putpixel((0, 0), (200, 30, 30, 255))
    sprite.save(tmp_path / "hero.png")

    picture = read_reference(tmp_path / "hero.png", 256)

    assert picture.mode == "RGB"
    assert picture.size == (256, 128)
    assert picture.getpixel((3, 3)) == (200, 30, 30)
    assert picture.getpixel((4, 4)) == (255, 255, 255)


def test_a_big_reference_keeps_its_size(tmp_path):
    Image.new("RGB", (1500, 1000)).save(tmp_path / "photo.png")

    assert read_reference(tmp_path / "photo.png", 1024).size == (1500, 1000)


def test_generate_takes_a_reference():
    args = parser().parse_args(["generate", "a knight", "--reference", "hero.png"])

    assert str(args.reference) == "hero.png"
