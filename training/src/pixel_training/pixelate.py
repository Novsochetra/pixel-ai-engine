from collections import Counter, deque

from PIL import Image

PALETTE_SIZE = 32
CLEAR = (0, 0, 0, 0)
# How far, in RGB, a colour may be from the border colour and still count as background:
# generated backgrounds are never one flat colour, they drift and carry noise.
BACKGROUND_DISTANCE = 48
# Outlines are one pixel wide, so a block often holds only part of one and the most common colour
# is what is next to it: the outline breaks. A clearly darker colour that covers this share of a
# block wins instead.
OUTLINE_SHARE = 0.25
OUTLINE_GAP = 40


def palette_of(sprite: Image.Image, background: tuple = (255, 255, 255)) -> Image.Image:
    """The colours of a sprite on its background, to snap other pictures of it to the same colours."""
    flat = Image.new("RGBA", sprite.size, background + (255,))
    flat.alpha_composite(sprite.convert("RGBA"))

    return flat.convert("RGB").quantize(colors=PALETTE_SIZE, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def block_mode(image: Image.Image, size: int, palette: Image.Image | None = None) -> Image.Image:
    # The most common colour of each block, not the average: averaging is what blurs pixel art.
    # With a palette (from palette_of), only its colours are used.
    if palette is None:
        paletted = image.convert("RGB").quantize(colors=PALETTE_SIZE, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    else:
        paletted = image.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
    block_width, block_height = image.width / size, image.height / size

    small = Image.new("P", (size, size))
    small.putpalette(paletted.getpalette())
    flat = paletted.getpalette()
    colors = [tuple(flat[index:index + 3]) for index in range(0, len(flat), 3)]

    for y in range(size):
        for x in range(size):
            box = (round(x * block_width), round(y * block_height), round((x + 1) * block_width), round((y + 1) * block_height))
            counts = paletted.crop(box).getcolors(maxcolors=256)
            small.putpixel((x, y), pick(counts, colors))

    return small.convert("RGBA")


def lightness(color: tuple) -> float:
    return 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]


def pick(counts: list[tuple[int, int]], colors: list[tuple]) -> int:
    """The colour for one block: the most common one, unless a clearly darker one (an outline) has its share."""
    main = max(counts)[1]
    total = sum(count for count, _ in counts)
    # A block of many colours, none with its share, keeps the most common one.
    shares = [index for count, index in counts if count >= OUTLINE_SHARE * total] or [main]
    darkest = min(shares, key=lambda index: lightness(colors[index]))

    return darkest if lightness(colors[darkest]) <= lightness(colors[main]) - OUTLINE_GAP else main


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
