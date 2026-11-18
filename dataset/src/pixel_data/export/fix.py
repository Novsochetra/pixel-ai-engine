from PIL import Image

SOLID_FROM = 128


def snap_alpha(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A").point(lambda value: 255 if value >= SOLID_FROM else 0)
    blank = Image.new("RGBA", image.size, (0, 0, 0, 0))

    solid = image.copy()
    solid.putalpha(alpha)

    return Image.composite(solid, blank, alpha)


def shrink(image: Image.Image, scale: int) -> Image.Image:
    if scale <= 1:
        return image

    return image.resize((image.width // scale, image.height // scale), Image.NEAREST)


def fixed(image: Image.Image, flags: list[str], scale: int) -> Image.Image:
    image = image.convert("RGBA")

    if "soft-edges" in flags:
        image = snap_alpha(image)

    if "upscaled" in flags:
        image = shrink(image, scale)

    return image
