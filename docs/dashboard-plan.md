# Dashboard plan: React UI + FastAPI

The dashboard moved out of `dataset/src/pixel_data/dashboard/` (Python that wrote HTML, served by
`pixel browse`) into two parts:

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

| Screen | Old page it replaced | Content | Inspector |
|---|---|---|---|
| Create | `/generate` | gallery of made characters | prompt, pose, facing, characters, sprite size, LoRAs and models |
| Rotate | part of `/training` try-outs | turned characters, each with its views side by side; segmented Turned, Try-outs | source, rotate LoRA, model, sprite size, views |
| Animate | `/animate` | sprite player: play, pause, fps, zoom, direction | character, actions |
| Landscape | (new) | gallery of backgrounds | prompt, size |
| Library | `/characters`, `/character`, `/flagged`, `/exports`, `/tryouts` | dataset grid; segmented filter All, Flagged, Exports, Try-outs; search | record details, labels |
| Training | `/training` | runs with loss charts | run details; new run, resume, try-out |

Selecting an image opens it large in a sheet, with zoom and download.

## API

Built (steps 1 to 6):

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
POST /api/{generated|animated}/trash        POST /api/{generated|animated}/restore
GET  /api/files/animated/{path}             GET  /api/files/uploads/{path}
GET  /api/animated                          GET  /api/animate/options
GET  /api/animate/sources                   POST /api/animate
POST /api/uploads?name=
GET  /api/runs                              GET  /api/training/options
POST /api/training/start      POST /api/training/resume     POST /api/training/tryout
GET  /api/rotated                           GET  /api/rotate/options
POST /api/rotate
```

Character and image ids hold slashes (`pac/train/0/front`), so they are the rest of the path.
`/api/thumbs/` shrinks a big picture to 256 px at most, nearest neighbour. `/api/files/` serves only
`.png` files inside `data/exports/`, `data/tryouts/`, `data/generated/` and `data/uploads/`, and
`.png` and `.gif` files inside `data/animated/`.

`POST /api/generate` takes JSON (`prompt`, `pose`, `facing`, `characters`, `sprite`, `drawWith`,
`drawingModel`, `turnWith`, `turningModel`) and checks it with `studio.generate_job`. A bad form
answers 400 and a second job while one runs answers 409, each with the reason in `detail`.
`/api/generate/options` lists the models, sprite sizes and facings from the same constants.

Delete on Create and Rotate calls `POST /api/generated/trash` (`folder`), and on Animate
`POST /api/animated/trash`: it moves `data/<kind>/<folder>/` to `data/trash/<kind>/`, so
`POST /api/<kind>/restore` (`folder`, `trashed`) can bring it back while the Undo toast shows. Each
card has a trash button in its corner, and the picture sheet a Delete at its bottom; both ask first.
Any other kind answers 400. A name that is not one folder answers 400,
a folder that is not there 404, and one a running job uses 409. Empty `data/trash/` by hand.

`POST /api/animate` takes JSON (`source`, `subject`, `views`, `actions` one a line, `size`,
`frames`) and checks it with `animate.animate_job`, with the same 400 and 409. The source is
`generated/<folder>/s<seed>` or `uploads/<file>`. `/api/animate/sources` lists both kinds, and
`/api/animate/options` the views, sizes, lengths, minutes a clip and limits from the constants in
`animate.py`. `/api/animated` lists the runs newest first; each clip names its view, action, kept
frames and the URLs of its GIF, raw GIF and sheet.

`POST /api/uploads` takes the PNG as the whole body (`Content-Type: image/png`, the file name in
`name`), as FastAPI's multipart forms need a package the project does not have. It answers 415 for
another type, 413 past 10 MB, and 400 for a file that is not a PNG or is too big a picture; it saves
with `animate.save_upload`.

`GET /api/runs` lists the runs newest first with `studio.read_runs`: each run's settings, the steps
done and planned, seconds a step, the latest `passes` (how many times over the data it has gone;
`null` in logs from before it was counted), checkpoints, final, the `loss` and `val` points as
`[step, value]`, the checkpoints a try-out may load, and `isTraining` for the run the running job
trains. `/api/training/options` lists the tasks, models, sizes and exports, each export with its
sources, licences and use, from the constants in `studio.py`.

`POST /api/training/start` takes JSON (`name`, `task`, `export`, `model`, `size`, `steps`, `sources`
as a list) and checks it with `studio.train_job`; `/api/training/resume` (`run`, `steps`, the step to
train to) with `studio.resume_job`; `/api/training/tryout` (`run`, `checkpoint`, `model`,
`characters`) with `studio.tryout_job`. Each answers 400 and 409 as Generate does. A resume keeps
the run's own settings, its `--more-exports`, `--more-repeat` and `--repeat` among them.

`POST /api/rotate` takes JSON (`source`, `lora`, `turningModel`, `sprite`, `views` as a list of
left, back and right) and checks it with `rotate_job.rotate_job`, with the same 400 and 409. The
source is a character with a front view, `generated/<folder>/s<seed>`, or `uploads/<file>`, from
`/api/animate/sources`; the LoRA must be a rotate one from `/api/loras?task=rotate`. It runs
`pixel-train rotate`, which writes a new folder under `data/generated/` in the layout `generate`
writes, with `rotated_from` in its `generated.json`, so Create, Animate and the Library list it too.
`/api/rotated` lists every character a rotate LoRA turned (by Rotate or by Generate) newest first,
each with its views in turning order; `/api/rotate/options` the models, sprite sizes, views and
upload limits from the same constants. The Rotate screen shows the rotate try-outs with the
Library's own try-out view, `/api/tryouts`, without their text-to-character pictures.

The job functions in `studio.py`, `animate.py` and `rotate_job.py` return the command to run. The
API calls them as they are and sends JSON. The records are read with `library.py`, `flagged.py`,
`exports.py` and `tryouts.py`.

## Order

1. Make `server/` and `ui/`: tokens, the base components, the layout shell (sidebar, toolbar,
   inspector) and the job status. One command runs both. Done.
2. Library (read only, so it is the safest first real screen). Done.
3. Create. Done.
4. Animate. Done.
5. Training. Done.
6. Rotate and Landscape, when their models are ready. Rotate done; Landscape waits for a landscape
   model and shows a placeholder that says so.
7. Remove the old HTML pages and `pixel browse`. Done: the server and the UI are the only dashboard.
