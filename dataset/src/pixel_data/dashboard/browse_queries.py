import json
import sqlite3
from dataclasses import dataclass

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


def imports(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("SELECT * FROM imports ORDER BY source").fetchall()
    views = db.execute("SELECT source, view, COUNT(*) AS count FROM images GROUP BY source, view").fetchall()

    summary = []
    for row in rows:
        counts = {view["view"]: view["count"] for view in views if view["source"] == row["source"]}
        ordered = dict(sorted(counts.items(), key=lambda item: view_order(item[0])))
        summary.append({**dict(row), "skipped": json.loads(row["skipped"]), "views": ordered})

    return summary


def splits(db: sqlite3.Connection) -> list[str]:
    rows = db.execute("SELECT DISTINCT source_split FROM images WHERE source_split IS NOT NULL ORDER BY 1")

    return [row[0] for row in rows]


def character_page(db: sqlite3.Connection, filters: Filters) -> tuple[list[dict], int]:
    where, values = where_clause(filters)
    total = db.execute(f"SELECT COUNT(DISTINCT character) FROM images {where}", values).fetchone()[0]

    offset = (filters.page - 1) * PAGE_SIZE
    rows = db.execute(
        f"SELECT character, source, MIN(caption) AS caption FROM images {where} "
        f"GROUP BY character ORDER BY MIN(rowid) LIMIT ? OFFSET ?",
        [*values, PAGE_SIZE, offset],
    ).fetchall()

    characters = [dict(row) for row in rows]
    attach_views(db, characters)

    return characters, total


def attach_views(db: sqlite3.Connection, characters: list[dict]) -> None:
    names = [character["character"] for character in characters]
    marks = ", ".join("?" for _ in names)
    rows = db.execute(f"SELECT id, character, view FROM images WHERE character IN ({marks})", names).fetchall()

    for character in characters:
        views = [dict(row) for row in rows if row["character"] == character["character"]]
        character["views"] = sorted(views, key=lambda view: view_order(view["view"]))


def character_images(db: sqlite3.Connection, character: str) -> list[dict]:
    rows = db.execute("SELECT * FROM images WHERE character = ?", (character,)).fetchall()

    return sorted((dict(row) for row in rows), key=lambda row: view_order(row["view"]))


def image_row(db: sqlite3.Connection, image_id: str):
    return db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
