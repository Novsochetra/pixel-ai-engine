# Pixel AI engine

A pixel art engine that runs locally: create a character from text, rotate it to 4 or 8 directions,
animate it, and make landscapes. Planned in ticket RAPA-2.

New to AI training? Start with the [beginner guide](docs/beginner-guide.md).

## Folders

Each step of building the engine gets its own folder:

| Folder | Step | Status |
|---|---|---|
| [`dataset/`](dataset/) | gather the image data, import it as records, analyze, annotate and export it, and browse it | gather, import, analyze, export and browser done; annotate later |
| [`training/`](training/) | try existing models (FLUX 3 Klein, FLUX.2 Klein 4B), then train on an export | try-out, LoRA training, generate, rotate and animate ready to run on the Mac |
| `engine/` | run the trained models: create, rotate, animate, landscape | later |
| [`server/`](server/) | the dashboard's API (FastAPI): jobs, records, images, exports, try-outs, Generate, Rotate, Animate and Training | steps 1 to 6 of [the dashboard plan](docs/dashboard-plan.md) done (Landscape waits for a model) |
| [`ui/`](ui/) | the dashboard (React): sidebar, inspector, job status, Library, Create, Rotate, Animate, Training; run `npm run dev` in `ui/` | steps 1 to 6 of [the dashboard plan](docs/dashboard-plan.md) done (Landscape waits for a model) |

## The four tasks

1. **Create:** text to character.
2. **Rotate:** one view to 4 or 8 views of the same character.
3. **Animate:** character and action to a sprite sheet.
4. **Landscape:** text to background.
