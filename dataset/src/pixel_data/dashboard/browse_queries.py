import json
import sqlite3
from dataclasses import dataclass

from pixel_data.dashboard.cache import until_changed
from pixel_data.records import view_order

PAGE_SIZE = 30


@dataclass
class Filters:
    source: str = ""
    split: str = ""
    search: str = ""
    page: int = 1


def where_clause(filters: Filters) -> tuple[str, list]:
    conditions, values = [], []

    if filters.source:
        conditions.append("source = ?")
        values.append(filters.source)

    if filters.split:
        conditions.append("source_split = ?")
        values.append(filters.split)

    if filters.search:
        conditions.append("(character LIKE ? OR caption LIKE ?)")
        values.extend([f"%{filters.search}%"] * 2)

    return (f"WHERE {' AND '.join(conditions)}" if conditions else ""), values


@until_changed
def imports(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("SELECT * FROM imports ORDER BY source").fetchall()
    views = db.execute("SELECT source, view, COUNT(*) AS count FROM images GROUP BY source, view").fetchall()

    summary = []
    for row in rows:
        counts = {view["view"]: view["count"] for view in views if view["source"] == row["source"]}
        ordered = dict(sorted(counts.items(), key=lambda item: view_order(item[0])))
        summary.append({**dict(row), "skipped": json.loads(row["skipped"]), "views": ordered})

    return summary


@until_changed
def splits(db: sqlite3.Connection) -> list[str]:
    rows = db.execute("SELECT DISTINCT source_split FROM characters WHERE source_split IS NOT NULL ORDER BY 1")

    return [row[0] for row in rows]


ACTION_ORDER = (None, "walk", "thrust", "slash")


def image_order(row: dict) -> tuple:
    action = row.get("action")
    rank = ACTION_ORDER.index(action) if action in ACTION_ORDER else len(ACTION_ORDER)

    return (rank, view_order(row["view"]))


def character_page(db: sqlite3.Connection, filters: Filters) -> tuple[list[dict], int]:
    where, values = where_clause(filters)
    total = count_characters(db, where, values)

    offset = (filters.page - 1) * PAGE_SIZE
    rows = db.execute(
        f"SELECT character, source, caption FROM characters {where} ORDER BY first_rowid LIMIT ? OFFSET ?",
        [*values, PAGE_SIZE, offset],
    ).fetchall()

    characters = [dict(row) for row in rows]
    attach_views(db, characters)

    return characters, total


@until_changed
def count_characters(db: sqlite3.Connection, where: str, values: list) -> int:
    return db.execute(f"SELECT COUNT(*) FROM characters {where}", values).fetchone()[0]


def attach_views(db: sqlite3.Connection, characters: list[dict]) -> None:
    names = [character["character"] for character in characters]
    marks = ", ".join("?" for _ in names)
    rows = db.execute(f"SELECT id, character, view, action, width FROM images WHERE character IN ({marks})", names).fetchall()

    for character in characters:
        views = [dict(row) for row in rows if row["character"] == character["character"]]
        character["views"] = sorted(views, key=image_order)


def character_images(db: sqlite3.Connection, character: str) -> list[dict]:
    rows = db.execute("SELECT * FROM images WHERE character = ?", (character,)).fetchall()

    return sorted((dict(row) for row in rows), key=image_order)


def image_row(db: sqlite3.Connection, image_id: str):
    return db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
