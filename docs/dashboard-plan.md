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
| Create | `/generate` | gallery of made characters | prompt, LoRA, size, steps, seed |
| Rotate | part of `/training` try-outs | one character, its 4 or 8 views side by side | source, directions |
| Animate | `/animate` | sprite player: play, pause, fps, zoom, direction | character, actions |
| Landscape | (new) | gallery of backgrounds | prompt, size |
| Library | `/characters`, `/character`, `/flagged`, `/exports`, `/tryouts` | dataset grid; segmented filter All, Flagged, Exports, Try-outs; search | record details, labels |
| Training | `/training` | runs with loss charts | run details; new run, resume, try-out |

Selecting an image opens it large in a sheet, with zoom and download.

## API (first cut)

```
GET  /api/characters?page=     GET  /api/characters/{id}     GET  /api/flagged
GET  /api/images/{id}.png      GET  /api/exports             GET  /api/tryouts
GET  /api/generated            GET  /api/animated            GET  /api/runs
GET  /api/loras?task=          GET  /api/jobs/current
POST /api/generate             POST /api/animate             POST /api/uploads
POST /api/training/start       POST /api/training/resume     POST /api/training/tryout
POST /api/jobs/stop
```

The job functions in `studio.py` and `animate_page.py` already return the command to run.
The API calls them as they are and sends JSON, not HTML.

## Order

1. Make `server/` and `ui/`: tokens, the base components, the layout shell (sidebar, toolbar,
   inspector) and the job status. One command runs both.
2. Library (read only, so it is the safest first real screen).
3. Create.
4. Animate.
5. Training.
6. Rotate and Landscape, when their models are ready.
7. Remove the old HTML pages and `pixel browse`.

The old dashboard keeps working until step 7.
