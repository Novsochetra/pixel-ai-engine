import sqlite3

from pixel_data.analyze.rules import FLAGS
from pixel_data.dashboard import flagged

from pixel_server.library.characters import split_flags
from pixel_server.library.urls import picture

EMPTY_FLAGGED = {"analyzed": False, "flags": [], "flag": "", "page": 1, "hasMore": False, "images": []}


def flagged_list(db: sqlite3.Connection, flag: str, page: int) -> dict:
    if not flagged.analyzed(db):
        return EMPTY_FLAGGED

    counts = flagged.flag_counts(db, "")
    chosen = flag if flag in counts else next(iter(counts), "")
    images = flagged.flagged_images(db, chosen, "", page) if chosen else []

    return {
        "analyzed": True,
        "flags": [flag_entry(name, count) for name, count in counts.items()],
        "flag": chosen,
        "page": page,
        "hasMore": len(images) == flagged.PAGE_SIZE,
        "images": [flagged_entry(image) for image in images],
    }


def flag_entry(name: str, count: int) -> dict:
    meaning, outcome = FLAGS[name]

    return {"name": name, "count": count, "meaning": meaning, "outcome": outcome}


def flagged_entry(image: dict) -> dict:
    return {
        **picture(image["id"], image["view"] or ""),
        "character": image["character"],
        "flags": split_flags(image["flags"]),
        "colors": image["colors"],
        "filled": image["filled"],
        "softEdge": image["soft_edge"],
    }
