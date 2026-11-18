import hashlib
from dataclasses import dataclass

from PIL import Image, ImageChops

SCALES = (8, 6, 5, 4, 3, 2)
LOOK_SIZE = 16
LOOK_LEVELS = 0b11100000


@dataclass
class Measures:
    width: int
    height: int
    filled: int
    soft_edge: int
    colors: int
    bbox: tuple[int, int, int, int] | None
    scale: int
    pixel_hash: str
    look_hash: str

    @property
    def touches_edge(self) -> bool:
        if self.bbox is None:
            return False

        left, top, right, _ = self.bbox

        # Characters stand with their feet on the bottom row, so only the other sides count.
        return left == 0 or top == 0 or right == self.width


def cleared(image: Image.Image) -> Image.Image:
    # Fully transparent pixels can hold any colour; make them all the same so equal-looking
    # pictures hash the same.
    alpha = image.getchannel("A")
    blank = Image.new("RGBA", image.size, (0, 0, 0, 0))

    return Image.composite(image, blank, alpha.point(lambda value: 255 if value else 0))


def alpha_counts(image: Image.Image) -> tuple[int, int]:
    histogram = image.getchannel("A").histogram()

    return sum(histogram[1:]), sum(histogram[1:255])


def visible_colors(image: Image.Image) -> int:
    colors = image.getcolors(maxcolors=image.width * image.height) or []

    return sum(1 for _, color in colors if color[3])


def pixel_scale(image: Image.Image) -> int:
    for scale in SCALES:
        if image.width % scale or image.height % scale:
            continue

        small = image.resize((image.width // scale, image.height // scale), Image.NEAREST)
        if ImageChops.difference(small.resize(image.size, Image.NEAREST), image).getbbox() is None:
            return scale

    return 1


def look_hash(image: Image.Image) -> str:
    # Small enough that a few changed pixels vanish, coarse enough in colour that
    # re-saving or slight shading changes do not matter.
    small = image.resize((LOOK_SIZE, LOOK_SIZE), Image.BOX)
    coarse = small.point(lambda value: value & LOOK_LEVELS)

    return hashlib.md5(coarse.tobytes()).hexdigest()


def measure(image: Image.Image) -> Measures:
    image = cleared(image.convert("RGBA"))
    filled, soft_edge = alpha_counts(image)

    return Measures(
        width=image.width,
        height=image.height,
        filled=filled,
        soft_edge=soft_edge,
        colors=visible_colors(image),
        bbox=image.getchannel("A").getbbox(),
        scale=pixel_scale(image),
        pixel_hash=hashlib.md5(image.tobytes()).hexdigest(),
        look_hash=look_hash(image),
    )
