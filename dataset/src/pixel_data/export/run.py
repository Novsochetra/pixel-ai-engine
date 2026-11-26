import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from pixel_data.analyze.store import ensure_schema
from pixel_data.export.select import select_characters
from pixel_data.export.split import SPLITS, assign_splits
from pixel_data.export.write import counts_by_split, leak_checks, write_character, write_files
from pixel_data.records import connect
from pixel_data.sources import Layout, Source, read_record

NAME = re.compile(r"[a-z0-9][a-z0-9_-]*")


def check_name(name: str) -> str:
    if not NAME.fullmatch(name):
        raise SystemExit("An export name uses only lowercase letters, digits, - and _, like rotation-v1.")

    return name


def chosen_sources(db, sources: list[Source], experimental: bool) -> list[Source]:
    analyzed = {row[0] for row in db.execute("SELECT DISTINCT i.source FROM images i JOIN analysis a ON a.id = i.id")}

    if not analyzed:
        raise SystemExit("Nothing analyzed yet. Run `pixel analyze` first.")

    # A held source never goes into training files, not even with --experimental.
    return [
        source
        for source in sources
        if source.id in analyzed and not source.is_held and (experimental or not source.is_experimental)
    ]


def fresh_folder(layout: Layout, name: str) -> Path:
    folder = layout.data / "exports" / name

    if folder.exists():
        shutil.rmtree(folder)

    folder.mkdir(parents=True)

    return folder


def source_notes(layout: Layout, sources: list[Source]) -> dict:
    notes = {}
    for source in sources:
        record = read_record(layout.source_dir(source)) or {}
        notes[source.id] = {"license": source.license, "use": source.use, "revision": record.get("revision", "")}

    return notes


def write_export(layout: Layout, name: str, characters: list[dict], splits: dict[str, str]) -> list[dict]:
    folder = fresh_folder(layout, name)

    entries = []
    for count, character in enumerate(characters, start=1):
        entries.append(write_character(folder, layout.raw, character, splits[character["character"]]))

        if count % 2000 == 0 or count == len(characters):
            print(f"\r  writing {count:,} of {len(characters):,} characters", end="", flush=True)

    print()

    return sorted(entries, key=lambda entry: SPLITS.index(entry["split"]))


def export(layout: Layout, sources: list[Source], name: str, include_check: bool, experimental: bool) -> dict:
    check_name(name)

    db = connect(layout.records)
    ensure_schema(db)

    try:
        picked = chosen_sources(db, sources, experimental)
        characters, left_out = select_characters(db, [source.id for source in picked], include_check)
    finally:
        db.close()

    splits = assign_splits(characters)
    entries = write_export(layout, name, characters, splits)

    summary = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "settings": {"include_check": include_check, "experimental": experimental},
        "sources": source_notes(layout, picked),
        "characters": counts_by_split(entries),
        "left_out": dict(left_out),
        "leaks": leak_checks(characters, splits),
    }
    write_files(layout.data / "exports" / name, entries, summary)

    return summary
