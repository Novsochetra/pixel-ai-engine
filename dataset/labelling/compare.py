"""Compare AI labels with the true LPC labels, fact by fact: body, man/woman, held items, hair colour.

    python3 labelling/compare.py <folder> <labels subfolder>

<folder> holds key.json from make_sheets.py; <labels subfolder> holds sheet-NNN.jsonl files ({"n": .., "label": ..}).
Clothes are not checked. The labels with a wrong fact go to <folder>/wrong-<labels subfolder>.json.
"""

import collections
import json
import re
import sys
from pathlib import Path

W = Path(sys.argv[1])
key = {item["n"]: item for item in json.loads((W / "key.json").read_text())}
labels = {}
for path in sorted((W / (sys.argv[2] if len(sys.argv) > 2 else "out")).glob("sheet-*.jsonl")):
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                row = json.loads(line)
                labels[int(row["n"])] = row["label"]
            except (ValueError, KeyError):
                pass

COLOURS = {"raven": ["black"], "brunette": ["brown"], "gold": ["blonde", "gold", "yellow"], "ruby": ["red"],
           "white blonde": ["white", "blonde", "platinum"], "light blonde": ["blonde", "yellow"], "dark blonde": ["blonde", "brown"],
           "chestnut": ["brown", "chestnut"], "redhead": ["red", "orange"], "orange": ["orange", "red"], "ginger": ["orange", "red"],
           "platinum": ["white", "platinum", "blonde"], "sandy": ["blonde", "brown", "sandy"], "strawberry": ["blonde", "red", "pink", "strawberry"]}
ALL_COLOURS = ["black", "brown", "blonde", "gold", "yellow", "red", "orange", "white", "gray", "grey", "silver", "blue", "green",
               "purple", "pink", "teal", "platinum", "chestnut", "violet", "lavender", "navy"]
WEAPONS = {"spear": r"spear|lance|pike|polearm|trident", "dagger": r"dagger|knife|blade|sword", "shield": r"shield"}


def body_of(label: str) -> str:
    if re.search(r"skelet|skull|bone", label):
        return "skeleton"
    if re.search(r"\borc|green[- ]skin|green-skinned|goblin", label):
        return "orc"
    if re.search(r"elf|(gray|grey|purple|lavender|blue|pale|violet|silver)[- ](skin|skinned)|gray-skinned|grey-skinned|purple-skinned", label):
        return "dark-elf"
    return "human"


def sex_of(label: str) -> str | None:
    if re.search(r"\b(woman|female|girl|lady)\b", label):
        return "female"
    if re.search(r"\b(man|male|boy|guy)\b", label):
        return "male"
    return None


facts = collections.Counter()
wrong_examples = []
wrong = 0
for n, item in sorted(key.items()):
    label = labels.get(n)
    truth = item["truth"]
    if label is None:
        facts["missing label"] += 1
        wrong += 1
        continue
    low = label.lower()
    problems = []

    sex, body = re.search(r"with (\w+) ([\w-]+) body", truth).groups()
    if body_of(low) != body:
        problems.append(f"body: says {body_of(low)}, is {body}")
    said = sex_of(low)
    facts["sex said" if said else "sex not said"] += 1
    if said and said != sex:
        problems.append(f"sex: says {said}, is {sex}")

    held = [w for w in WEAPONS if re.search(rf"with {w}\b", truth)]
    for weapon in held:
        if not re.search(WEAPONS[weapon], low):
            problems.append(f"missed {weapon}")
    for weapon, pattern in WEAPONS.items():
        if weapon not in held and re.search(pattern, low) and not (weapon == "dagger" and "dagger" not in low and "sword" in low and held):
            problems.append(f"extra {weapon}")

    hair = re.search(r"with ([\w -]+?) (?:hairstyle|loose hair)", truth)
    if hair and "hair" in low:
        name = hair.group(1)
        expected = next((v for k, v in COLOURS.items() if name.startswith(k)), [name.split()[0]])
        near = re.findall(r"(\w+)(?:[- ]\w+)?(?:,? \w+)? hair", low)
        named = [c for c in ALL_COLOURS if any(c in w for w in near)]
        if named and not any(c in expected or (c == "grey" and "gray" in expected) for c in named):
            problems.append(f"hair: says {named[0]}, is {name}")

    for problem in problems:
        facts[problem.split(":")[0].split(" ")[0] if ":" in problem else problem] += 1
    if problems:
        wrong += 1
        wrong_examples.append((n, item["sheet"], label, truth.removeprefix("lpc-style pixel art character, "), problems))

print(f"labels written: {len(labels)} of {len(key)}")
print(f"labels with at least one wrong fact: {wrong} ({100 * wrong / len(key):.1f}%)")
print("by fact:", dict(facts.most_common()))
(W / f"wrong-{sys.argv[2] if len(sys.argv) > 2 else 'out'}.json").write_text(json.dumps(wrong_examples, indent=1))
for example in wrong_examples[:12]:
    print(example)
