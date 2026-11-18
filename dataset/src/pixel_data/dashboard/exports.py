import json
import random
from html import escape
from pathlib import Path

from pixel_data.dashboard.browse_pages import link, readable_time
from pixel_data.export.split import SPLITS

SAMPLES_PER_SPLIT = 6


def read_exports(folder: Path) -> list[dict]:
    summaries = []
    for summary in sorted(folder.glob("*/export.json")):
        summaries.append(json.loads(summary.read_text()))

    return sorted(summaries, key=lambda summary: summary["created_at"], reverse=True)


def samples(folder: Path, name: str) -> dict[str, list[dict]]:
    by_split = {split: [] for split in SPLITS}

    with (folder / name / "characters.jsonl").open() as handle:
        for line in handle:
            entry = json.loads(line)
            by_split[entry["split"]].append(entry)

    # The same picks on every visit, so a reload does not reshuffle what you were looking at.
    pick = random.Random(name)

    return {split: pick.sample(entries, min(SAMPLES_PER_SPLIT, len(entries))) for split, entries in by_split.items()}


def counts_table(summary: dict) -> str:
    sources = sorted({source for counts in summary["characters"].values() for source in counts})
    header = "".join(f"<th>{escape(source)}</th>" for source in sources)

    rows = []
    for split in SPLITS:
        counts = summary["characters"].get(split, {})
        cells = "".join(f"<td>{counts.get(source, 0):,}</td>" for source in sources)
        rows.append(f"<tr><th>{split}</th>{cells}<td><b>{sum(counts.values()):,}</b></td></tr>")

    return f'<div class="table"><table><thead><tr><th></th>{header}<th>all</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def leak_line(leaks: dict) -> str:
    clean = not any(leaks.values())
    state = "ok" if clean else "drop"
    words = "no character, group or picture is in two splits" if clean else (
        f"{leaks['groups_in_two_splits']} groups and {leaks['pictures_in_two_splits']} pictures are in two splits"
    )

    return f'<p><span class="outcome {state}">{"pass" if clean else "leak"}</span> Leak check: {words}.</p>'


def sample_rows(name: str, picks: dict[str, list[dict]]) -> str:
    blocks = []
    for split, entries in picks.items():
        characters = []
        for entry in entries:
            views = "".join(
                f'<figure class="view"><img src="{link(f"/exports/{name}/{path}")}" alt="{view}" loading="lazy"><figcaption>{view}</figcaption></figure>'
                for view, path in entry["views"].items()
            )
            characters.append(f'<article class="row"><header><a href="{link("/character", id=entry["character"])}">{escape(entry["character"])}</a></header><div class="views">{views}</div></article>')

        blocks.append(f'<h3>{split}</h3><section class="rows">{"".join(characters)}</section>')

    return "".join(blocks)


def export_card(folder: Path, summary: dict) -> str:
    name = summary["name"]
    left_out = ", ".join(f"{count:,} {reason}" for reason, count in summary["left_out"].items()) or "nothing"
    licences = ", ".join(f"{source}: {note['license']}" for source, note in summary["sources"].items())

    return f"""<section class="card export">
<h2>{escape(name)}</h2><p class="muted">Made {escape(readable_time(summary['created_at']))} · folder <code>data/exports/{escape(name)}</code></p>
{counts_table(summary)}{leak_line(summary['leaks'])}
<p class="muted">Left out: {escape(left_out)}.</p><p class="muted">Licences: {escape(licences)}.</p>
<h2>Samples</h2>{sample_rows(name, samples(folder, name))}</section>"""


def exports_page(folder: Path) -> str:
    summaries = read_exports(folder) if folder.exists() else []

    if not summaries:
        return "<h1>No exports yet</h1><p>Run <code>uv run pixel export</code>, then reload.</p>"

    return "<h1>Exports</h1>" + "".join(export_card(folder, summary) for summary in summaries)
