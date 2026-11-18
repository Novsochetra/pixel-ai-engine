from collections import Counter

from pixel_data.analyze.duplicates import mark_duplicates
from pixel_data.analyze.measure import measure
from pixel_data.analyze.rules import image_flags, status_of
from pixel_data.analyze.store import clear_source, ensure_schema, write_measures
from pixel_data.images import load_image
from pixel_data.records import connect
from pixel_data.sources import Layout

BATCH = 2000


def imported_sources(db) -> list[str]:
    return [row["source"] for row in db.execute("SELECT source FROM imports ORDER BY source")]


def measured_row(layout: Layout, row) -> tuple:
    measures = measure(load_image(layout.raw, row))
    flags = image_flags(measures)
    bbox = ",".join(str(value) for value in measures.bbox) if measures.bbox else None

    return (
        row["id"], measures.filled, measures.soft_edge, measures.colors, bbox, measures.scale,
        measures.pixel_hash, measures.look_hash, ",".join(flags), ",".join(flags), status_of(flags),
    )


def analyze_source(db, layout: Layout, source: str) -> int:
    rows = db.execute("SELECT * FROM images WHERE source = ? ORDER BY rowid", (source,)).fetchall()

    with db:
        clear_source(db, source)

        for start in range(0, len(rows), BATCH):
            write_measures(db, [measured_row(layout, row) for row in rows[start:start + BATCH]])
            print(f"\r  {source}: {min(start + BATCH, len(rows)):,} of {len(rows):,}", end="", flush=True)

    print()

    return len(rows)


def check_sources(chosen: list[str], imported: list[str]) -> list[str]:
    missing = [source for source in chosen if source not in imported]

    if missing:
        raise SystemExit(f"Not imported yet: {', '.join(missing)}. Run `pixel import {' '.join(missing)}` first.")

    return chosen or imported


def analyze(layout: Layout, chosen: list[str]) -> dict:
    db = connect(layout.records)
    ensure_schema(db)

    try:
        for source in check_sources(chosen, imported_sources(db)):
            analyze_source(db, layout, source)

        with db:
            copies, groups = mark_duplicates(db)

        return {"copies": copies, "groups": groups, "summary": summary(db)}
    finally:
        db.close()


def summary(db) -> dict[str, Counter]:
    rows = db.execute("SELECT i.source, a.status, a.flags FROM analysis a JOIN images i ON i.id = a.id")

    counts = {}
    for row in rows:
        source = counts.setdefault(row["source"], Counter())
        source[f"status:{row['status']}"] += 1

        for flag in filter(None, row["flags"].split(",")):
            source[flag] += 1

    return counts
