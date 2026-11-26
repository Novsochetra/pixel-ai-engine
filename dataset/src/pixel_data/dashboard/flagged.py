import sqlite3

from pixel_data.analyze.rules import FLAGS
from pixel_data.dashboard.cache import until_changed

PAGE_SIZE = 60


def analyzed(db: sqlite3.Connection) -> bool:
    table = db.execute("SELECT name FROM sqlite_master WHERE name = 'analysis'").fetchone()

    return bool(table) and db.execute("SELECT 1 FROM analysis LIMIT 1").fetchone() is not None


@until_changed
def status_counts(db: sqlite3.Connection) -> dict[str, dict[str, int]]:
    rows = db.execute(
        "SELECT i.source, a.status, COUNT(*) AS count FROM analysis a JOIN images i ON i.id = a.id GROUP BY 1, 2"
    )

    counts = {}
    for row in rows:
        counts.setdefault(row["source"], {})[row["status"]] = row["count"]

    return counts


@until_changed
def flag_counts(db: sqlite3.Connection, source: str) -> dict[str, int]:
    where, values = ("WHERE i.source = ?", [source]) if source else ("", [])
    rows = db.execute(f"SELECT a.flags FROM analysis a JOIN images i ON i.id = a.id {where}", values)

    counts = dict.fromkeys(FLAGS, 0)
    for row in rows:
        for flag in filter(None, row["flags"].split(",")):
            counts[flag] += 1

    return {flag: count for flag, count in counts.items() if count}


@until_changed
def flagged_images(db: sqlite3.Connection, flag: str, source: str, page: int) -> list[dict]:
    rows = db.execute(
        "SELECT i.id, i.character, i.view, a.flags, a.colors, a.filled, a.soft_edge FROM analysis a "
        "JOIN images i ON i.id = a.id WHERE (',' || a.flags || ',') LIKE ? AND (? = '' OR i.source = ?) "
        "ORDER BY i.rowid LIMIT ? OFFSET ?",
        (f"%,{flag},%", source, source, PAGE_SIZE, (page - 1) * PAGE_SIZE),
    )

    return [dict(row) for row in rows]


def character_analysis(db: sqlite3.Connection, character: str) -> tuple[dict, dict | None]:
    if not analyzed(db):
        return {}, None

    rows = db.execute(
        "SELECT a.* FROM analysis a JOIN images i ON i.id = a.id WHERE i.character = ?", (character,)
    ).fetchall()
    group = db.execute("SELECT * FROM character_groups WHERE character = ?", (character,)).fetchone()

    return {row["id"]: dict(row) for row in rows}, dict(group) if group else None
