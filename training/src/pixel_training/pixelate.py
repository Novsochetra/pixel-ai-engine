from collections import Counter, deque

from PIL import Image

PALETTE_SIZE = 32
CLEAR = (0, 0, 0, 0)
# How far, in RGB, a colour may be from the border colour and still count as background:
# generated backgrounds are never one flat colour, they drift and carry noise.
BACKGROUND_DISTANCE = 48


def block_mode(image: Image.Image, size: int) -> Image.Image:
    # The most common colour of each block, not the average: averaging is what blurs pixel art.
    paletted = image.convert("RGB").quantize(colors=PALETTE_SIZE, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    block_width, block_height = image.width / size, image.height / size

    small = Image.new("P", (size, size))
    small.putpalette(paletted.getpalette())

    for y in range(size):
        for x in range(size):
            box = (round(x * block_width), round(y * block_height), round((x + 1) * block_width), round((y + 1) * block_height))
            counts = paletted.crop(box).getcolors(maxcolors=PALETTE_SIZE + 1)
            small.putpixel((x, y), max(counts)[1])

    return small.convert("RGBA")


def border_color(image: Image.Image) -> tuple:
    width, height = image.size
    edge = [(x, 0) for x in range(width)] + [(x, height - 1) for x in range(width)]
    edge += [(0, y) for y in range(height)] + [(width - 1, y) for y in range(height)]

    return Counter(image.getpixel(point) for point in edge).most_common(1)[0][0]


def near(color: tuple, background: tuple) -> bool:
    return sum((a - b) ** 2 for a, b in zip(color[:3], background[:3])) <= BACKGROUND_DISTANCE**2


def clear_background(image: Image.Image) -> Image.Image:
    # Only background that reaches the border goes: the same colour inside the character
    # (a white shirt on a white background) stays.
    image = image.copy()
    background = border_color(image)
    width, height = image.size

    queue = deque((x, y) for x in range(width) for y in (0, height - 1))
    queue.extend((x, y) for x in (0, width - 1) for y in range(height))
    seen = set()

    while queue:
        point = queue.popleft()
        if point in seen or not (0 <= point[0] < width and 0 <= point[1] < height):
            continue

        seen.add(point)
        if not near(image.getpixel(point), background):
            continue

        image.putpixel(point, CLEAR)
        x, y = point
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return image


def pixelate(image: Image.Image, size: int) -> Image.Image:
    return clear_background(block_mode(image, size))


def blow_up(image: Image.Image, size: int, background: tuple = (255, 255, 255)) -> Image.Image:
    flat = Image.new("RGBA", image.size, background + (255,))
    flat.alpha_composite(image.convert("RGBA"))

    return flat.convert("RGB").resize((size, size), Image.NEAREST)
