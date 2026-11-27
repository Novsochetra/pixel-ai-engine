from collections import Counter
from dataclasses import dataclass

from PIL import Image

# The classic palettes as Lospec lists them (lospec.com/palette-list). dataset's studio.PALETTES
# names the same keys for the dashboard.
PALETTES = {
    "1-bit": ["000000", "ffffff"],
    "game-boy": ["081820", "346856", "88c070", "e0f8d0"],
    "cga": ["000000", "ff55ff", "55ffff", "ffffff"],
    "pico-8": ["000000", "1d2b53", "7e2553", "008751", "ab5236", "5f574f", "c2c3c7", "fff1e8", "ff004d", "ffa300",
               "ffec27", "00e436", "29adff", "83769c", "ff77a8", "ffccaa"],
    "commodore-64": ["000000", "626262", "898989", "adadad", "ffffff", "9f4e44", "cb7e75", "6d5412", "a1683c",
                     "c9d487", "9ae29b", "5cab5e", "6abfc6", "887ecb", "50459b", "a057a3"],
    "zx-spectrum": ["000000", "0000d8", "0000ff", "d80000", "ff0000", "d800d8", "ff00ff", "00d800", "00ff00",
                    "00d8d8", "00ffff", "d8d800", "ffff00", "d8d8d8", "ffffff"],
    "nes": ["000000", "fcfcfc", "f8f8f8", "bcbcbc", "7c7c7c", "a4e4fc", "3cbcfc", "0078f8", "0000fc", "b8b8f8",
            "6888fc", "0058f8", "0000bc", "d8b8f8", "9878f8", "6844fc", "4428bc", "f8b8f8", "f878f8", "d800cc",
            "940084", "f8a4c0", "f85898", "e40058", "a80020", "f0d0b0", "f87858", "f83800", "a81000", "fce0a8",
            "fca044", "e45c10", "881400", "f8d878", "f8b800", "ac7c00", "503000", "d8f878", "b8f818", "00b800",
            "007800", "b8f8b8", "58d854", "00a800", "006800", "b8f8d8", "58f898", "00a844", "005800", "00fcfc",
            "00e8d8", "008888", "004058", "f8d8f8", "787878"],
}
# These are shades of one colour, so a picture goes onto them by lightness: by RGB distance a red
# dragon is nearest the darkest green and comes out a black shape.
SHADES = {"1-bit", "game-boy"}
NO_PALETTE = "none"
MOST_COLOURS = 32
FEWEST_COLOURS = 2
MAX_COLOURS = 64


@dataclass(frozen=True)
class Colours:
    palette: str = NO_PALETTE
    most: int = MOST_COLOURS


def rgb(code: str) -> tuple[int, int, int]:
    return int(code[0:2], 16), int(code[2:4], 16), int(code[4:6], 16)


def palette_image(name: str) -> Image.Image | None:
    if name == NO_PALETTE:
        return None

    colors = [rgb(code) for code in PALETTES[name]]
    flat = [channel for color in colors for channel in color]
    image = Image.new("P", (1, 1))
    # Pillow fills a short palette with black, which would join in as a colour no palette chose.
    image.putpalette(flat + flat[:3] * (256 - len(colors)))

    return image


def distance(one: tuple, other: tuple) -> int:
    return sum((a - b) ** 2 for a, b in zip(one[:3], other[:3]))


def kept_colours(counts: Counter, most: int, has_palette: bool) -> list[tuple]:
    # A palette's colours stay as they are, so the most used of them are kept. Without one, median
    # cut finds the few colours that stand for all of them, rare ones such as eyes included.
    if has_palette:
        return [color for color, _ in counts.most_common(most)]

    strip = Image.new("RGB", (len(counts), 1))
    strip.putdata(list(counts))
    flat = strip.quantize(colors=most, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).getpalette()

    return [tuple(flat[index:index + 3]) for index in range(0, min(len(flat), most * 3), 3)]


# The background is gone by now, so the limit counts only the character's own colours.
def limit_colours(sprite: Image.Image, colours: Colours) -> Image.Image:
    pixels = list(sprite.get_flattened_data())
    counts = Counter(pixel[:3] for pixel in pixels if pixel[3])
    if len(counts) <= colours.most:
        return sprite

    kept = kept_colours(counts, colours.most, colours.palette != NO_PALETTE)
    nearest = {color: min(kept, key=lambda option: distance(color, option)) for color in counts}
    limited = sprite.copy()
    limited.putdata([nearest[pixel[:3]] + (255,) if pixel[3] else pixel for pixel in pixels])

    return limited
