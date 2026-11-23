# Labelling prompt (v2)

The prompt each Haiku 5.5 agent got (medium effort). Change the sheet list, the output folder and
the first number in the example line for each agent.

```text
You label pixel art characters for an image-model training set.

Folder: <the folder from make_sheets.py>

Your sheets (in sheets/): sheet-001.png ... sheet-013.png

Each sheet is a 4x4 grid of small fantasy RPG characters, front view, each cell numbered "#N" at the top left.

For each sheet, one at a time:
1. Read the sheet image with the Read tool.
2. Look at each character slowly, part by part, then write one short label in simple English, 8-25 words. Rules:
   - Body: if you see bones, a skull face or ribs, it is "a skeleton". Otherwise name the skin colour exactly: light, tan, dark brown, green (say "a green-skinned orc"), or lavender/purple-gray (say "a purple-skinned elf"). Never use the vague word "pale".
   - Do NOT say man, woman, boy, girl, male or female. Use "a character" or "a person" instead.
   - Hair: its colour and style. If a helmet or hood hides it, name the helmet or hood instead.
   - Clothes: the main pieces with their colours.
   - Held items: check both hands and both hips. A dagger is small: a short gray or brown blade, often low at one side of the body. A spear is a long horizontal pole with a metal tip. A shield is a round or square board on one arm. Name each one you see. Do not name an item that is not there.
   Examples:
   "a green-skinned orc with long brown hair in a purple dress, holding a small dagger"
   "a purple-skinned elf with a metal helmet, brown vest and teal pants, holding a round wooden shield"
   "a skeleton with gray hair in a black robe, holding a long spear"
   Do not mention pixel art, the background or the view.
3. Write the labels for that sheet to out2/<sheet name>.jsonl, one JSON object per line: {"n": 1, "label": "..."}. "n" is the number in the cell. One line per character.

Write each sheet's file before you read the next sheet. Do not read any other files. When all your sheets are done, reply with only: the sheet files you wrote and how many labels in total.
```
