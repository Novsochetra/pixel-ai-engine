import json
from html import escape
from pathlib import Path

from pixel_data.dashboard.browse_pages import link, readable_time


def read_runs(folder: Path) -> list[dict]:
    runs = [json.loads(path.read_text()) for path in folder.glob("*/results.json")] if folder.exists() else []

    return sorted(runs, key=lambda run: run["created_at"], reverse=True)


def picture(run: str, path: str | None, label: str, pixel: bool = False) -> str:
    if not path:
        return f'<figure class="view"><div class="missing">none</div><figcaption>{escape(label)}</figcaption></figure>'

    size_class = " pixel" if pixel else ""

    return f'<figure class="view{size_class}"><img src="{link(f"/tryouts/{run}/{path}")}" alt="{escape(label)}" loading="lazy"><figcaption>{escape(label)}</figcaption></figure>'


def model_rows(run: dict) -> str:
    rows = []
    for name, result in run["models"].items():
        if "error" in result:
            state = f'<span class="outcome drop">failed</span> {escape(result["error"][:300])}'
        elif result.get("pending"):
            state = '<span class="outcome check">not run yet</span>'
        else:
            state = f'<span class="outcome ok">done</span> loaded in {result["load_seconds"]}s · {result["seconds_per_image"]}s per image'

        rows.append(f"<tr><th>{escape(name)}</th><td>{escape(run.get('repos', {}).get(name, ''))}</td><td>{state}</td></tr>")

    return f'<div class="table"><table><tbody>{"".join(rows)}</tbody></table></div>'


def finished_models(run: dict) -> list[str]:
    return [name for name, result in run["models"].items() if "create" in result]


def create_section(run: dict) -> str:
    blocks = []
    for job in run["create"]:
        figures = []
        for model in finished_models(run):
            for seed in run["seeds"]:
                output = run["models"][model]["create"].get(f"{job['id']}-s{seed}", {})
                figures.append(picture(run["name"], output.get("raw"), f"{model} #{seed}"))
                figures.append(picture(run["name"], output.get("pixel"), "64px", pixel=True))

        blocks.append(f'<article class="row"><header><span class="muted">{escape(job["prompt"])}</span></header><div class="views">{"".join(figures)}</div></article>')

    return f'<h2>Create: text to character</h2><section class="rows wide">{"".join(blocks)}</section>'


def rotate_section(run: dict) -> str:
    if not run["rotate"]:
        return ""

    blocks = []
    for job in run["rotate"]:
        figures = [picture(run["name"], job["front"], "front given", pixel=True), picture(run["name"], job["truth"], f"real {job['view']}", pixel=True)]
        for model in finished_models(run):
            output = run["models"][model]["rotate"].get(job["id"], {})
            figures.append(picture(run["name"], output.get("pixel"), f"{model}", pixel=True))

        title = f'<a href="{link("/character", id=job["character"])}">{escape(job["character"])}</a> → {escape(job["view"])}'
        blocks.append(f'<article class="row"><header>{title}</header><div class="views">{"".join(figures)}</div></article>')

    return f'<h2>Rotate: front view to another view, test characters</h2><section class="rows">{"".join(blocks)}</section>'


def run_links(runs: list[dict], chosen: str) -> str:
    links = [
        f'<a class="chip{" on" if run["name"] == chosen else ""}" href="{link("/tryouts", run=run["name"])}">{escape(run["name"])}</a>'
        for run in runs
    ]

    return f'<nav class="chips">{"".join(links)}</nav>'


def tryouts_page(folder: Path, chosen: str) -> str:
    runs = read_runs(folder)

    if not runs:
        return "<h1>No try-outs yet</h1><p>In <code>training/</code>, run <code>uv run pixel-train tryout</code>, then reload.</p>"

    run = next((run for run in runs if run["name"] == chosen), runs[0])
    when = escape(readable_time(run["created_at"]))

    return (
        f'<h1>Try-outs</h1>{run_links(runs, run["name"])}'
        f'<p class="muted">{when} · on {escape(run.get("device", "?"))}</p>{model_rows(run)}'
        f"{create_section(run)}{rotate_section(run)}"
    )
