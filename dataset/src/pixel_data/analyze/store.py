import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis (
  id TEXT PRIMARY KEY,
  filled INTEGER NOT NULL,
  soft_edge INTEGER NOT NULL,
  colors INTEGER NOT NULL,
  bbox TEXT,
  scale INTEGER NOT NULL,
  pixel_hash TEXT NOT NULL,
  look_hash TEXT NOT NULL,
  image_flags TEXT NOT NULL,
  flags TEXT NOT NULL,
  status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS analysis_by_status ON analysis (status);
CREATE TABLE IF NOT EXISTS character_groups (
  character TEXT PRIMARY KEY,
  group_id TEXT NOT NULL,
  group_size INTEGER NOT NULL,
  copy_of TEXT
);
"""


def ensure_schema(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA)


def clear_source(db: sqlite3.Connection, source: str) -> None:
    db.execute("DELETE FROM analysis WHERE id IN (SELECT id FROM images WHERE source = ?)", (source,))


def write_measures(db: sqlite3.Connection, rows: list[tuple]) -> None:
    db.executemany(
        "INSERT OR REPLACE INTO analysis VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )


def split_flags(text: str) -> list[str]:
    return [flag for flag in text.split(",") if flag]
