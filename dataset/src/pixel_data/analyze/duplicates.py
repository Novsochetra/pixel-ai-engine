import hashlib
import sqlite3
from collections import defaultdict

from pixel_data.analyze.rules import status_of
from pixel_data.analyze.store import split_flags


def character_keys(db: sqlite3.Connection) -> tuple[dict, dict, dict]:
    rows = db.execute(
        "SELECT i.character, i.view, a.pixel_hash, a.look_hash, a.filled FROM images i "
        "JOIN analysis a ON a.id = i.id ORDER BY i.rowid"
    )

    exact, look, pictures = defaultdict(list), defaultdict(list), defaultdict(set)
    for row in rows:
        exact[row["character"]].append(f"{row['view']}:{row['pixel_hash']}")
        look[row["character"]].append(f"{row['view']}:{row['look_hash']}")

        if row["filled"]:
            pictures[row["pixel_hash"]].add(row["character"])

    return digest(exact), digest(look), pictures


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


class Groups:
    def __init__(self, order: list[str]):
        self.rank = {character: index for index, character in enumerate(order)}
        self.parent = {}

    def root(self, character: str) -> str:
        while self.parent.get(character, character) != character:
            character = self.parent[character]

        return character

    def join(self, characters: list[str]) -> None:
        roots = sorted({self.root(character) for character in characters}, key=self.rank.get)

        for other in roots[1:]:
            self.parent[other] = roots[0]


def find_groups(look: dict[str, str], pictures: dict[str, set], copies: dict[str, str]) -> dict[str, list[str]]:
    kept = [character for character in look if character not in copies]
    groups = Groups(kept)

    # Near-identical characters, and characters sharing even one identical view, must never
    # end up on both sides of the train/test split.
    same_look = defaultdict(list)
    for character in kept:
        same_look[look[character]].append(character)

    for members in [*same_look.values(), *pictures.values()]:
        groups.join([character for character in members if character not in copies])

    members = defaultdict(list)
    for character in kept:
        members[groups.root(character)].append(character)

    return {first: group for first, group in members.items() if len(group) > 1}


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
    exact, look, pictures = character_keys(db)
    copies = find_copies(exact)
    groups = find_groups(look, pictures, copies)

    write_groups(db, groups, copies)
    apply_flags(db, {character for group in groups.values() for character in group}, copies)

    return len(copies), len(groups)
