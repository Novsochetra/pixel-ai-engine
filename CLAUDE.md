# Project rules

A local pixel art engine: `dataset/` (data), `training/` (models), `server/` (FastAPI), `ui/`
(React dashboard). See `README.md` and `docs/dashboard-plan.md`.

You and every subagent follow the four rule files below with care. Hand each subagent this file.

## Commands

| Command | Where | What it runs |
|---|---|---|
| `npm run dev` | `ui/` | the server on http://127.0.0.1:8780 and Vite on http://localhost:5180, both reloading |
| `npm run check` | `ui/` | ESLint, Stylelint, Prettier, types, every test and the build; run it before done |
| `uv run ruff check` | `server/` | the Python lint |
| `uv run pytest` | `server/`, `dataset/`, `training/` | the Python tests |

## Coding

@docs/coding-style.md

- The rules hold for Python too: a why is a short `#` comment, never a docstring that says what the
  code does.
- Files stay under 150 lines, functions under 40, complexity under 10, depth 3, at most 4 parameters.
  ESLint holds `ui/` to it; `ruff` holds complexity and parameters in `server/`.
- `server/` keeps routes thin and puts logic in plain functions. It reuses `pixel_data` from
  `dataset/` and never imports the models: jobs run `pixel-train` as a separate process.
- `ui/` takes colors, type, radii, shadows, blur and motion only from `ui/src/styles/tokens.css`.
  No raw hex anywhere else (Stylelint).
- Never install packages without asking.

## UI

@docs/ui-guidelines.md

## Testing

@docs/testing.md

- `ui/` tests live in `ui/test/unit/`, `ui/test/integration/` and `ui/test/regression/` (Vitest).
- `server/` tests live in `server/tests/unit/`, `server/tests/integration/` and
  `server/tests/regression/` (pytest).

## Versions

@docs/versioning.md

- Each part has its own version: `ui/package.json`, `server/pyproject.toml`,
  `dataset/pyproject.toml`, `training/pyproject.toml`.
- Raise it in the part users see change. A new screen, tool or API route is minor; fixes and polish
  are patch; breaking saved data (`dataset/data/`) or an API the UI calls is major.
