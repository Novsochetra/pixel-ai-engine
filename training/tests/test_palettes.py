import pytest
from PIL import Image

from pixel_training.cli import parser
from pixel_training.palettes import PALETTES, Colours, rgb
from pixel_training.pixelate import pixelate

WHITE = (255, 255, 255)


def stripes(colors: list[tuple]) -> Image.Image:
    # Square, as the model draws, with a white border, so the background is found and cleared;
    # then one stripe per colour.
    side = len(colors) * 8 + 16
    image = Image.new("RGB", (side, side), WHITE)
    for index, color in enumerate(colors):
        image.paste(color, (8 + index * 8, 8, 16 + index * 8, side - 8))

    return image


def opaque_colours(sprite: Image.Image) -> set[tuple]:
    return {pixel[:3] for pixel in sprite.get_flattened_data() if pixel[3]}


def test_the_palettes_have_the_sizes_the_form_names():
    sizes = {name: len(set(codes)) for name, codes in PALETTES.items()}

    assert sizes == {"1-bit": 2, "game-boy": 4, "cga": 4, "pico-8": 16, "commodore-64": 16, "zx-spectrum": 15,
                     "nes": 55}


def test_a_sprite_on_a_palette_uses_only_its_colours():
    picture = stripes([(200, 40, 50), (30, 120, 60), (240, 200, 40), (60, 70, 160)])

    sprite = pixelate(picture, picture.width, Colours("pico-8"))

    assert opaque_colours(sprite) <= {rgb(code) for code in PALETTES["pico-8"]}
    assert len(opaque_colours(sprite)) == 4


def test_a_shades_palette_keeps_how_light_each_colour_is():
    picture = stripes([(200, 40, 50), (150, 200, 120)])

    sprite = pixelate(picture, picture.width, Colours("game-boy"))

    assert opaque_colours(sprite) == {rgb("346856"), rgb("88c070")}


def test_max_colours_keeps_the_most_used_colours_of_a_palette():
    picture = stripes([(0, 0, 0), (0, 0, 0), (0, 0, 0), (255, 0, 77), (255, 0, 77), (41, 173, 255)])

    sprite = pixelate(picture, picture.width, Colours("pico-8", 2))

    assert opaque_colours(sprite) == {(0, 0, 0), (255, 0, 77)}


def test_max_colours_without_a_palette_limits_the_character_not_the_background():
    picture = stripes([(200, 0, 0), (0, 200, 0), (0, 0, 200), (200, 200, 0), (0, 200, 200), (200, 0, 200)])

    sprite = pixelate(picture, picture.width, Colours(most=3))

    assert len(opaque_colours(sprite)) == 3
    assert sprite.getpixel((0, 0))[3] == 0


def test_no_palette_and_32_colours_draw_as_before():
    picture = stripes([(200, 40, 50), (30, 120, 60)])

    assert pixelate(picture, 8).tobytes() == pixelate(picture, 8, Colours()).tobytes()


def test_more_than_32_colours_are_kept_when_asked():
    colors = [(index * 5, 255 - index * 5, (index * 37) % 256) for index in range(40)]
    picture = stripes(colors)

    assert len(opaque_colours(pixelate(picture, picture.width, Colours(most=64)))) == 40
    assert len(opaque_colours(pixelate(picture, picture.width))) <= 32


def test_generate_takes_a_palette_and_a_colour_limit():
    plain = parser().parse_args(["generate", "a knight"])
    chosen = parser().parse_args(["generate", "a knight", "--palette", "nes", "--colours", "16"])

    assert (plain.palette, plain.colours) == ("none", 32)
    assert (chosen.palette, chosen.colours) == ("nes", 16)
    for count in ("1", "65", "lots"):
        with pytest.raises(SystemExit):
            parser().parse_args(["generate", "a knight", "--colours", count])
