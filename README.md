# Pixel AI engine

A pixel art engine that runs locally: create a character from text, rotate it to 4 or 8 directions,
animate it, and make landscapes. Planned in ticket RAPA-2.

New to AI training? Start with the [beginner guide](docs/beginner-guide.md).

## Folders

Each step of building the engine gets its own folder:

| Folder | Step | Status |
|---|---|---|
| [`dataset/`](dataset/) | gather the image data, import it as records, analyze, annotate and export it | gather, import, analyze and export done; annotate later |
| [`training/`](training/) | try existing models (FLUX 3 Klein, FLUX.2 Klein 4B), then train on an export | try-out, LoRA training, generate, rotate and animate ready to run on the Mac |
| `engine/` | run the trained models: create, rotate, animate, landscape | later |
| [`server/`](server/) | the dashboard's API (FastAPI): jobs, records, images, exports, try-outs, Generate, Rotate, Animate and Training | steps 1 to 7 of [the dashboard plan](docs/dashboard-plan.md) done (Landscape waits for a model) |
| [`ui/`](ui/) | the dashboard (React): sidebar, inspector, job status, Library, Create, Rotate, Animate, Training | steps 1 to 7 of [the dashboard plan](docs/dashboard-plan.md) done (Landscape waits for a model) |

## Open the dashboard

```bash
cd ui && npm install && npm run build      # once, and again after the UI changes
cd ../server && uv run pixel-server        # then open http://127.0.0.1:8780
```

While working on the dashboard itself, run `npm run dev` in `ui/` instead: it starts the server on
http://127.0.0.1:8780 and the UI on http://localhost:5180, and both reload on a change.

## The four tasks

1. **Create:** text to character.
2. **Rotate:** one view to 4 or 8 views of the same character.
3. **Animate:** character and action to a sprite sheet.
4. **Landscape:** text to background.
