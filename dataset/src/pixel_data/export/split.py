import hashlib

SPLITS = ("train", "val", "test")
SHARES = {"train": 90, "val": 5}


def bucket(group: str) -> str:
    # A hash of the group's name, not a shuffle: the same group lands in the same split on
    # every export, even after new data is added.
    point = int(hashlib.md5(group.encode()).hexdigest(), 16) % 100

    if point < SHARES["train"]:
        return "train"

    return "val" if point < SHARES["train"] + SHARES["val"] else "test"


def assign_splits(characters: list[dict]) -> dict[str, str]:
    groups = {}
    for character in characters:
        groups.setdefault(character["group"], []).append(character)

    splits = {}
    for group, members in groups.items():
        # A source's own test set stays test, and pulls its whole group along with it.
        held_out = any(member["source_split"] == "test" or member["use"] == "eval" for member in members)
        split = "test" if held_out else bucket(group)

        for member in members:
            splits[member["character"]] = split

    return splits
