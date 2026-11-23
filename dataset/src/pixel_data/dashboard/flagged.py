import sqlite3
from html import escape

from pixel_data.analyze.rules import FLAGS
from pixel_data.dashboard.browse_pages import link, select
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


def image_tile(image: dict) -> str:
    flags = ", ".join(filter(None, image["flags"].split(",")))
    facts = f"{image['colors']} colours · {image['filled']} px · {image['soft_edge']} soft"

    return f"""<a class="tile-link" href="{link('/character', id=image['character'])}">
<img src="{link('/image', id=image['id'])}" alt="{escape(image['id'])}" loading="lazy">
<span>{escape(image['id'])}</span><span class="muted">{escape(flags)}</span><span class="muted">{facts}</span></a>"""


def flag_chips(counts: dict[str, int], chosen: str, source: str) -> str:
    chips = []
    for flag, count in counts.items():
        meaning, outcome = FLAGS[flag]
        state = " on" if flag == chosen else ""
        chips.append(
            f'<a class="chip{state}" href="{link("/flagged", flag=flag, source=source)}" title="{escape(meaning)}">'
            f'{escape(flag)} <b>{count:,}</b> <span class="outcome {outcome}">{outcome}</span></a>'
        )

    return f'<nav class="chips">{"".join(chips)}</nav>'


def flagged_page(db: sqlite3.Connection, flag: str, source: str, page: int, sources: list[str]) -> str:
    if not analyzed(db):
        return "<h1>Not analyzed yet</h1><p>Run <code>uv run pixel analyze</code>, then reload.</p>"

    counts = flag_counts(db, source)
    flag = flag if flag in counts else next(iter(counts), "")
    images = flagged_images(db, flag, source, page) if flag else []

    form = f'<form class="filters" method="get" action="/flagged"><input type="hidden" name="flag" value="{escape(flag)}">{select("source", "All sources", sources, source)}</form>'
    meaning = f"<p>{escape(FLAGS[flag][0])}.</p>" if flag else "<p>Nothing flagged.</p>"
    tiles = "".join(image_tile(image) for image in images)
    more = f'<a href="{link("/flagged", flag=flag, source=source, page=page + 1)}">Next {PAGE_SIZE} →</a>' if len(images) == PAGE_SIZE else ""

    return f'<h1>Flagged</h1>{form}{flag_chips(counts, flag, source)}{meaning}<section class="tiles">{tiles}</section><p>{more}</p>'


def character_analysis(db: sqlite3.Connection, character: str) -> tuple[dict, dict | None]:
    if not analyzed(db):
        return {}, None

    rows = db.execute(
        "SELECT a.* FROM analysis a JOIN images i ON i.id = a.id WHERE i.character = ?", (character,)
    ).fetchall()
    group = db.execute("SELECT * FROM character_groups WHERE character = ?", (character,)).fetchone()

    return {row["id"]: dict(row) for row in rows}, dict(group) if group else None


def group_note(db: sqlite3.Connection, group: dict | None) -> str:
    if group is None:
        return ""

    if group["copy_of"]:
        original = group["copy_of"]
        return f'<p class="note">Exact copy of <a href="{link("/character", id=original)}">{escape(original)}</a>, so it is dropped.</p>'

    rows = db.execute("SELECT character FROM character_groups WHERE group_id = ? AND copy_of IS NULL", (group["group_id"],))
    others = [row["character"] for row in rows]
    names = ", ".join(f'<a href="{link("/character", id=name)}">{escape(name)}</a>' for name in others)

    return f'<p class="note">Near-identical group, kept together in the split: {names}</p>'
