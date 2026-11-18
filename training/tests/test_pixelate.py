from PIL import Image

from pixel_training.pixelate import blow_up, clear_background, pixelate

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
