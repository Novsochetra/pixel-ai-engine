from pixel_data.analyze.measure import Measures

ALMOST_EMPTY = 16
MOST_COLORS = 256

STATUS_ORDER = ("ok", "fix", "check", "drop")

# Each flag: what it means to a person, and what happens to the image.
FLAGS = {
    "empty": ("nothing drawn", "drop"),
    "almost-empty": (f"fewer than {ALMOST_EMPTY} pixels drawn", "drop"),
    "duplicate": ("the same character as another one, pixel for pixel", "drop"),
    "touches-edge": ("drawing reaches the left, top or right border, may be cut off", "check"),
    "too-many-colors": (f"more than {MOST_COLORS} colours, may not be pixel art", "check"),
    "soft-edges": ("half-transparent pixels, pixel art has none", "fix"),
    "upscaled": ("drawn at 2x or more, can be shrunk to its true size", "fix"),
    "near-duplicate": ("looks almost the same as another character, kept on one side of the split", "ok"),
}


def image_flags(measures: Measures) -> list[str]:
    if measures.filled == 0:
        return ["empty"]

    checks = {
        "almost-empty": measures.filled < ALMOST_EMPTY,
        "touches-edge": measures.touches_edge,
        "too-many-colors": measures.colors > MOST_COLORS,
        "soft-edges": measures.soft_edge > 0,
        "upscaled": measures.scale > 1,
    }

    return [flag for flag, raised in checks.items() if raised]


def status_of(flags: list[str]) -> str:
    statuses = [FLAGS[flag][1] for flag in flags] or ["ok"]

    return max(statuses, key=STATUS_ORDER.index)
