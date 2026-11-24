# Pixel AI engine

A pixel art engine that runs locally: create a character from text, rotate it to 4 or 8 directions,
animate it, and make landscapes. Planned in ticket RAPA-2.

New to AI training? Start with the [beginner guide](docs/beginner-guide.md).

## Folders

Each step of building the engine gets its own folder:

| Folder | Step | Status |
|---|---|---|
| [`dataset/`](dataset/) | gather the image data, import it as records, analyze, annotate and export it, and browse it | gather, import, analyze, export and browser done; annotate later |
| [`training/`](training/) | try existing models (FLUX 3 Klein, FLUX.2 Klein 4B), then train on an export | try-out and LoRA training (rotate) ready to run on the Mac |
| `engine/` | run the trained models: create, rotate, animate, landscape | later |

## The four tasks

1. **Create:** text to character.
2. **Rotate:** one view to 4 or 8 views of the same character.
3. **Animate:** character and action to a sprite sheet.
4. **Landscape:** text to background.
