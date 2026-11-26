# Dashboard plan: React UI + FastAPI

The dashboard moves out of `dataset/src/pixel_data/dashboard/` (Python that writes HTML) into two parts:

| Folder | What | Stack |
|---|---|---|
| `server/` | the API: images, records, jobs (generate, train, animate) | Python, FastAPI, reuses `pixel_data` |
| `ui/` | the dashboard you see | React 19, TypeScript, Vite, react-router, TanStack Query, motion |

UI rules: [ui-guidelines.md](ui-guidelines.md) (Apple HIG). The components look and move like the
Retro Arcade's (buttons, segmented control, sheet, notice, glass, tokens). The layout is our own.

## Layout

A creative tool, like Pixelmator or Final Cut: the art in the middle, settings on the right.

```
┌─────────────┬──────────────────────────────────────────┬──────────────┐
│ Pixel Engine│ Create          [Grid|Large]   [Generate]│ Inspector    │
│             ├──────────────────────────────────────────┤              │
│ MAKE        │                                          │ Prompt       │
│  Create     │                                          │ Model (LoRA) │
│  Rotate     │        content: gallery, player,         │ Size, steps  │
│  Animate    │        chart, grid                        │ Seed         │
│  Landscape  │                                          │              │
│ DATA        │                                          │ Selected:    │
│  Library    │                                          │ details      │
│  Training   │                                          │              │
│             │                                          │              │
│ ▸ Job 42%   │                                          │              │
└─────────────┴──────────────────────────────────────────┴──────────────┘
```

- **Sidebar:** sections in two groups. At the bottom, the running job with a progress bar.
  Click it for a popover with the log and Stop.
- **Toolbar:** screen title, a segmented control for the view, one primary action.
- **Content:** the pixel art, big and sharp.
- **Inspector:** the form for a new job, or the details of the selected item. It can hide.
- **Narrow screens:** bottom tab bar, and the inspector opens as a sheet.

## Screens

| Screen | Replaces | Content | Inspector |
|---|---|---|---|
| Create | `/generate` | gallery of made characters | prompt, pose, facing, characters, sprite size, LoRAs and models |
| Rotate | part of `/training` try-outs | one character, its 4 or 8 views side by side | source, directions |
| Animate | `/animate` | sprite player: play, pause, fps, zoom, direction | character, actions |
| Landscape | (new) | gallery of backgrounds | prompt, size |
| Library | `/characters`, `/character`, `/flagged`, `/exports`, `/tryouts` | dataset grid; segmented filter All, Flagged, Exports, Try-outs; search | record details, labels |
| Training | `/training` | runs with loss charts | run details; new run, resume, try-out |

Selecting an image opens it large in a sheet, with zoom and download.

## API

Built (steps 1 to 3):

```
GET  /api/health                            GET  /api/jobs/current      POST /api/jobs/stop
GET  /api/characters?page=&q=&source=&split=
GET  /api/characters/{id}                   GET  /api/flagged?flag=&page=
GET  /api/exports                           GET  /api/tryouts?run=
GET  /api/images/{id}.png                   GET  /api/thumbs/{id}.png
GET  /api/files/exports/{path}              GET  /api/files/tryouts/{path}
GET  /api/files/generated/{path}            GET  /api/generated
GET  /api/generate/options                  GET  /api/loras?task=create|rotate
POST /api/generate
```

Character and image ids hold slashes (`pac/train/0/front`), so they are the rest of the path.
`/api/thumbs/` shrinks a big picture to 256 px at most, nearest neighbour. `/api/files/` serves only
`.png` files inside `data/exports/`, `data/tryouts/` and `data/generated/`.

`POST /api/generate` takes JSON (`prompt`, `pose`, `facing`, `characters`, `sprite`, `drawWith`,
`drawingModel`, `turnWith`, `turningModel`) and checks it with `studio.generate_job`. A bad form
answers 400 and a second job while one runs answers 409, each with the reason in `detail`.
`/api/generate/options` lists the models, sprite sizes and facings from the same constants.

Still to build:

```
GET  /api/animated            GET  /api/runs
POST /api/animate             POST /api/uploads
POST /api/training/start      POST /api/training/resume     POST /api/training/tryout
```

The job functions in `studio.py` and `animate_page.py` already return the command to run.
The API calls them as they are and sends JSON, not HTML.

## Order

1. Make `server/` and `ui/`: tokens, the base components, the layout shell (sidebar, toolbar,
   inspector) and the job status. One command runs both. Done.
2. Library (read only, so it is the safest first real screen). Done.
3. Create. Done.
4. Animate.
5. Training.
6. Rotate and Landscape, when their models are ready.
7. Remove the old HTML pages and `pixel browse`.

The old dashboard keeps working until step 7.
