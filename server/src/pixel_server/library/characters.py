import sqlite3

from pixel_data.dashboard import browse_queries as queries
from pixel_data.dashboard import flagged
from pixel_data.dashboard.browse_pages import view_label

from pixel_server.library.urls import picture

EMPTY_LIST = {"characters": [], "total": 0, "page": 1, "pages": 1, "sources": [], "splits": []}
RECORD_FIELDS = ("view", "action", "width", "height", "file", "member", "crop", "license", "use")


def character_list(db: sqlite3.Connection, filters: queries.Filters) -> dict:
    rows, total = queries.character_page(db, filters)

    return {
        "characters": [list_entry(row) for row in rows],
        "total": total,
        "page": filters.page,
        "pages": max(1, -(-total // queries.PAGE_SIZE)),
        "sources": [entry["source"] for entry in queries.imports(db)],
        "splits": queries.splits(db),
    }


def list_entry(row: dict) -> dict:
    return {
        "id": row["character"],
        "source": row["source"],
        "caption": row["caption"] or "",
        "views": [picture(view["id"], view_label(view)) for view in row["views"]],
    }


def character_detail(db: sqlite3.Connection, name: str) -> dict | None:
    images = queries.character_images(db, name)
    if not images:
        return None

    analysis, group = flagged.character_analysis(db, name)

    return {
        "id": name,
        "source": images[0]["source"],
        "split": images[0]["source_split"],
        "caption": images[0]["caption"] or "",
        "analyzed": flagged.analyzed(db),
        "images": [image_entry(image, analysis.get(image["id"])) for image in images],
        "group": group_entry(db, group),
    }


def image_entry(image: dict, analysis: dict | None) -> dict:
    record = {field: image[field] for field in RECORD_FIELDS}

    return {**picture(image["id"], view_label(image)), **record, "analysis": analysis_entry(analysis)}


def analysis_entry(analysis: dict | None) -> dict | None:
    if analysis is None:
        return None

    return {
        "status": analysis["status"],
        "flags": split_flags(analysis["flags"]),
        "colors": analysis["colors"],
        "filled": analysis["filled"],
        "softEdge": analysis["soft_edge"],
        "scale": analysis["scale"],
    }


def split_flags(flags: str) -> list[str]:
    return [flag for flag in flags.split(",") if flag]


def group_entry(db: sqlite3.Connection, group: dict | None) -> dict | None:
    if group is None:
        return None

    if group["copy_of"]:
        return {"kind": "copy", "characters": [group["copy_of"]]}

    rows = db.execute(
        "SELECT character FROM character_groups WHERE group_id = ? AND copy_of IS NULL", (group["group_id"],)
    )

    return {"kind": "group", "characters": [row["character"] for row in rows]}
