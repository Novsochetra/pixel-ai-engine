from PIL import Image

from pixel_training.pixelate import blow_up, block_mode, clear_background, pixelate

WHITE = (255, 255, 255, 255)
RED = (200, 30, 30, 255)


def sprite() -> Image.Image:
    image = Image.new("RGBA", (8, 8), WHITE)
    for x, y in ((3, 2), (4, 2), (3, 3), (4, 3), (2, 4), (5, 4), (3, 5), (4, 5)):
        image.putpixel((x, y), RED)

    return image


def test_a_cleanly_scaled_up_sprite_comes_back_pixel_for_pixel():
    original = sprite()
    big = original.resize((128, 128), Image.NEAREST)

    small = pixelate(big, 8)

    assert small.tobytes() == clear_background(original).tobytes()
    assert small.getpixel((0, 0)) == (0, 0, 0, 0)
    assert small.getpixel((3, 4)) == WHITE


def test_noise_inside_a_block_does_not_change_its_colour():
    big = sprite().resize((128, 128), Image.NEAREST)
    for offset in range(5):
        big.putpixel((50 + offset, 40), (10, 200, 10, 255))

    assert pixelate(big, 8).getpixel((3, 2)) == RED


def test_background_inside_the_character_stays():
    image = Image.new("RGBA", (5, 5), WHITE)
    for x in range(1, 4):
        for y in range(1, 4):
            image.putpixel((x, y), RED)
    image.putpixel((2, 2), WHITE)

    cleared = clear_background(image)

    assert cleared.getpixel((0, 0)) == (0, 0, 0, 0)
    assert cleared.getpixel((2, 2)) == WHITE


def test_a_sprite_is_scaled_up_on_white_for_the_model():
    small = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    small.putpixel((0, 0), RED)

    big = blow_up(small, 16)

    assert big.mode == "RGB" and big.size == (16, 16)
    assert big.getpixel((3, 3)) == RED[:3]
    assert big.getpixel((12, 12)) == (255, 255, 255)


def test_a_background_that_drifts_in_colour_is_still_cleared():
    image = Image.new("RGBA", (6, 6), (240, 240, 240, 255))
    image.putpixel((0, 5), (225, 228, 222, 255))
    image.putpixel((5, 0), (250, 250, 250, 255))
    image.putpixel((3, 3), RED)

    cleared = clear_background(image)

    assert cleared.getpixel((0, 5)) == (0, 0, 0, 0)
    assert cleared.getpixel((5, 0)) == (0, 0, 0, 0)
    assert cleared.getpixel((3, 3)) == RED


def test_a_thin_outline_that_misses_the_grid_is_kept():
    # A 1-pixel black line on a 4x4 grid, so it covers only a quarter of each block it crosses.
    image = Image.new("RGB", (32, 32), (255, 255, 255))
    for y in range(32):
        image.putpixel((13, y), (0, 0, 0))
    for x in range(14, 32):
        for y in range(32):
            image.putpixel((x, y), (200, 30, 30))

    small = block_mode(image, 8)

    assert small.getpixel((3, 4))[:3] == (0, 0, 0)
    assert small.getpixel((5, 4))[:3] == (200, 30, 30)


def test_a_dark_speck_inside_a_block_does_not_take_it_over():
    image = Image.new("RGB", (8, 8), (200, 30, 30))
    image.putpixel((1, 1), (0, 0, 0))

    assert block_mode(image, 2).getpixel((0, 0))[:3] == (200, 30, 30)


def test_a_block_of_many_colours_keeps_the_most_common_one():
    image = Image.new("RGB", (5, 1), (200, 30, 30))
    for x, color in enumerate([(0, 0, 0), (0, 0, 200), (0, 200, 0)]):
        image.putpixel((x, 0), color)
    image = image.resize((5, 5), Image.NEAREST).crop((0, 0, 5, 5))

    assert block_mode(image, 1).getpixel((0, 0))[:3] == (200, 30, 30)
