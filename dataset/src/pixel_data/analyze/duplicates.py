import hashlib
import sqlite3
from collections import defaultdict

from pixel_data.analyze.rules import status_of
from pixel_data.analyze.store import split_flags


def character_keys(db: sqlite3.Connection) -> tuple[dict, dict]:
    rows = db.execute(
        "SELECT i.character, i.view, a.pixel_hash, a.look_hash FROM images i "
        "JOIN analysis a ON a.id = i.id ORDER BY i.rowid"
    )

    exact, look = defaultdict(list), defaultdict(list)
    for row in rows:
        exact[row["character"]].append(f"{row['view']}:{row['pixel_hash']}")
        look[row["character"]].append(f"{row['view']}:{row['look_hash']}")

    return digest(exact), digest(look)


def digest(parts: dict[str, list[str]]) -> dict[str, str]:
    return {character: hashlib.md5("|".join(sorted(keys)).encode()).hexdigest() for character, keys in parts.items()}


def find_copies(exact: dict[str, str]) -> dict[str, str]:
    first_with_key, copies = {}, {}

    for character, key in exact.items():
        if key in first_with_key:
            copies[character] = first_with_key[key]
        else:
            first_with_key[key] = character

    return copies


def find_groups(look: dict[str, str], copies: dict[str, str]) -> dict[str, list[str]]:
    members = defaultdict(list)

    for character, key in look.items():
        if character not in copies:
            members[key].append(character)

    return {group[0]: group for group in members.values() if len(group) > 1}


def write_groups(db: sqlite3.Connection, groups: dict[str, list[str]], copies: dict[str, str]) -> None:
    rows = [(character, first, len(group), None) for first, group in groups.items() for character in group]
    rows += [(character, original, 1, original) for character, original in copies.items()]

    db.execute("DELETE FROM character_groups")
    db.executemany("INSERT INTO character_groups VALUES (?, ?, ?, ?)", rows)


def group_flag(character: str, grouped: set[str], copies: dict[str, str]) -> list[str]:
    if character in copies:
        return ["duplicate"]

    return ["near-duplicate"] if character in grouped else []


def apply_flags(db: sqlite3.Connection, grouped: set[str], copies: dict[str, str]) -> None:
    rows = db.execute(
        "SELECT a.id, a.image_flags, i.character FROM analysis a JOIN images i ON i.id = a.id"
    ).fetchall()

    updates = []
    for row in rows:
        flags = split_flags(row["image_flags"]) + group_flag(row["character"], grouped, copies)
        updates.append((",".join(flags), status_of(flags), row["id"]))

    db.executemany("UPDATE analysis SET flags = ?, status = ? WHERE id = ?", updates)


def mark_duplicates(db: sqlite3.Connection) -> tuple[int, int]:
    exact, look = character_keys(db)
    copies = find_copies(exact)
    groups = find_groups(look, copies)

    write_groups(db, groups, copies)
    apply_flags(db, {character for group in groups.values() for character in group}, copies)

    return len(copies), len(groups)
