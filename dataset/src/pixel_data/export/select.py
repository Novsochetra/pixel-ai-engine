import sqlite3
from collections import Counter

REQUIRED_VIEWS = ("front", "left", "back", "right")


def image_rows(db: sqlite3.Connection, sources: list[str]) -> list:
    marks = ", ".join("?" for _ in sources)

    return db.execute(
        "SELECT i.*, a.flags, a.status, a.scale, a.pixel_hash, g.group_id FROM images i "
        "JOIN analysis a ON a.id = i.id LEFT JOIN character_groups g ON g.character = i.character "
        # Only the four turnable views: not action strips (lpc-action), icons or scenes.
        f"WHERE i.source IN ({marks}) AND i.action IS NULL AND i.view IN ({', '.join('?' for _ in REQUIRED_VIEWS)}) "
        "ORDER BY i.rowid",
        [*sources, *REQUIRED_VIEWS],
    ).fetchall()


def by_character(rows: list) -> dict[str, list]:
    characters = {}
    for row in rows:
        characters.setdefault(row["character"], []).append(row)

    return characters


def reason_to_leave_out(views: list, allowed: set[str]) -> str | None:
    present = {view["view"] for view in views}

    if not set(REQUIRED_VIEWS) <= present:
        return "missing a view"

    worst = {view["status"] for view in views if view["view"] in REQUIRED_VIEWS}

    if "drop" in worst:
        return "a view is dropped"

    if not worst <= allowed:
        return "a view needs checking"

    return None


def character_entry(name: str, views: list) -> dict:
    first = views[0]
    kept = {view["view"]: dict(view) for view in views if view["view"] in REQUIRED_VIEWS}

    return {
        "character": name,
        "source": first["source"],
        "source_split": first["source_split"],
        "use": first["use"],
        "license": first["license"],
        "caption": first["caption"],
        "group": first["group_id"] or name,
        "views": kept,
    }


def select_characters(db: sqlite3.Connection, sources: list[str], include_check: bool) -> tuple[list[dict], Counter]:
    allowed = {"ok", "fix", "check"} if include_check else {"ok", "fix"}

    chosen, left_out = [], Counter()
    for name, views in by_character(image_rows(db, sources)).items():
        reason = reason_to_leave_out(views, allowed)

        if reason:
            left_out[reason] += 1
        else:
            chosen.append(character_entry(name, views))

    return chosen, left_out
