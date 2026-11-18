import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

VIEWS = ("front", "front-left", "left", "back-left", "back", "back-right", "right", "front-right")

SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  character TEXT NOT NULL,
  view TEXT,
  action TEXT,
  frame INTEGER,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  file TEXT NOT NULL,
  member TEXT,
  data_offset INTEGER,
  data_length INTEGER,
  crop TEXT,
  caption TEXT,
  license TEXT NOT NULL,
  use TEXT NOT NULL,
  source_split TEXT
);
CREATE INDEX IF NOT EXISTS images_by_character ON images (source, character);
CREATE INDEX IF NOT EXISTS images_by_view ON images (view);
CREATE TABLE IF NOT EXISTS imports (
  source TEXT PRIMARY KEY,
  imported_at TEXT NOT NULL,
  images INTEGER NOT NULL,
  characters INTEGER NOT NULL,
  skipped TEXT NOT NULL
);
"""


@dataclass
class Record:
    id: str
    source: str
    character: str
    view: str | None
    width: int
    height: int
    file: str
    license: str
    use: str
    member: str | None = None
    data_offset: int | None = None
    data_length: int | None = None
    crop: str | None = None
    caption: str | None = None
    action: str | None = None
    frame: int | None = None
    source_split: str | None = None


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)

    return db


def replace_source(db: sqlite3.Connection, source: str, records: Iterable[Record]) -> int:
    columns = list(Record.__dataclass_fields__)
    insert = f"INSERT INTO images ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"

    with db:
        db.execute("DELETE FROM images WHERE source = ?", (source,))
        cursor = db.executemany(insert, ([asdict(record)[name] for name in columns] for record in records))

    return cursor.rowcount


def log_import(db: sqlite3.Connection, source: str, skipped: dict[str, int]) -> dict:
    counts = db.execute(
        "SELECT COUNT(*) AS images, COUNT(DISTINCT character) AS characters FROM images WHERE source = ?",
        (source,),
    ).fetchone()
    entry = {
        "source": source,
        "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "images": counts["images"],
        "characters": counts["characters"],
        "skipped": json.dumps(skipped),
    }

    with db:
        db.execute(
            "INSERT OR REPLACE INTO imports VALUES (:source, :imported_at, :images, :characters, :skipped)", entry
        )

    return entry


def view_order(view: str | None) -> int:
    return VIEWS.index(view) if view in VIEWS else len(VIEWS)
