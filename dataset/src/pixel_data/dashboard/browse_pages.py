from datetime import datetime
from html import escape
from urllib.parse import urlencode

from pixel_data.analyze.rules import STATUS_ORDER
from pixel_data.dashboard.browse_queries import PAGE_SIZE, Filters


def link(path: str, **params) -> str:
    query = urlencode({key: value for key, value in params.items() if value not in ("", None)})

    return escape(f"{path}?{query}" if query else path)


def layout(title: str, body: str, has_downloads: bool) -> str:
    downloads = '<a href="/downloads">Downloads</a>' if has_downloads else ""

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title><link rel="stylesheet" href="/style.css"></head>
<body><nav class="top"><strong>Pixel engine data</strong><a href="/">Imported</a><a href="/characters">Characters</a><a href="/flagged">Flagged</a><a href="/exports">Exports</a><a href="/tryouts">Try-outs</a>{downloads}</nav>
<main>{body}</main></body></html>"""


def view_image(view: dict, size_class: str = "") -> str:
    src = link("/image", id=view["id"])
    label = escape(view["view"] or "")

    return f'<figure class="view {size_class}"><img src="{src}" alt="{label}" loading="lazy"><figcaption>{label}</figcaption></figure>'


def readable_time(stamp: str) -> str:
    return datetime.fromisoformat(stamp).strftime("%Y-%m-%d %H:%M UTC")


def status_line(counts: dict[str, int]) -> str:
    parts = [f'<span class="outcome {status}">{status}</span> {counts.get(status, 0):,}' for status in STATUS_ORDER]

    return f'<p class="statuses">{" ".join(parts)}</p>'


def import_card(entry: dict, statuses: dict[str, int] | None) -> str:
    views = "".join(f"<li>{escape(view)} <b>{count:,}</b></li>" for view, count in entry["views"].items())
    skipped = "".join(f"<li>{escape(reason)}: <b>{count:,}</b></li>" for reason, count in entry["skipped"].items())
    skipped_block = f'<h3>Skipped</h3><ul class="counts">{skipped}</ul>' if skipped else '<p class="muted">Nothing skipped.</p>'

    return f"""<article class="card">
<h2><a href="{link('/characters', source=entry['source'])}">{escape(entry['source'])}</a></h2>
<p class="big">{entry['characters']:,} characters · {entry['images']:,} images</p>
<p class="muted">Imported {escape(readable_time(entry['imported_at']))}</p>
{status_line(statuses) if statuses else '<p class="muted">Not analyzed yet: run <code>uv run pixel analyze</code>.</p>'}
<h3>Images per view</h3><ul class="counts">{views}</ul>{skipped_block}</article>"""


def home_page(entries: list[dict], statuses: dict[str, dict[str, int]]) -> str:
    if not entries:
        return '<h1>Nothing imported yet</h1><p>Run <code>uv run pixel import pac lpc-4view</code>, then reload.</p>'

    cards = "".join(import_card(entry, statuses.get(entry["source"])) for entry in entries)

    return f'<h1>Imported sources</h1><section class="cards">{cards}</section>'


def select(name: str, label: str, options: list[str], chosen: str) -> str:
    items = [f'<option value="">{escape(label)}</option>']
    items += [f'<option{" selected" if option == chosen else ""}>{escape(option)}</option>' for option in options]

    return f'<select name="{name}" onchange="this.form.submit()">{"".join(items)}</select>'


def filter_form(filters: Filters, sources: list[str], splits: list[str]) -> str:
    return f"""<form class="filters" method="get" action="/characters">
{select("source", "All sources", sources, filters.source)}
{select("split", "All splits", splits, filters.split)}
<input type="search" name="q" value="{escape(filters.search)}" placeholder="Search captions or ids">
<button>Search</button></form>"""


def character_row(character: dict) -> str:
    views = "".join(view_image(view) for view in character["views"])
    caption = escape(character["caption"] or "")

    return f"""<article class="row">
<header><a href="{link('/character', id=character['character'])}">{escape(character['character'])}</a>
<span class="muted">{caption}</span></header><div class="views">{views}</div></article>"""


def pager(filters: Filters, total: int) -> str:
    pages = max(1, -(-total // PAGE_SIZE))
    params = {"source": filters.source, "split": filters.split, "q": filters.search}
    back = f'<a href="{link("/characters", **params, page=filters.page - 1)}">← Previous</a>' if filters.page > 1 else ""
    forward = f'<a href="{link("/characters", **params, page=filters.page + 1)}">Next →</a>' if filters.page < pages else ""

    return f'<nav class="pager">{back}<span>Page {filters.page} of {pages:,} · {total:,} characters</span>{forward}</nav>'


def characters_page(characters: list[dict], total: int, filters: Filters, sources: list[str], splits: list[str]) -> str:
    rows = "".join(character_row(character) for character in characters)
    listing = f'<section class="rows">{rows}</section>' if rows else '<p class="muted">No characters match.</p>'

    return f"<h1>Characters</h1>{filter_form(filters, sources, splits)}{pager(filters, total)}{listing}{pager(filters, total)}"


def detail_rows(image: dict) -> str:
    fields = ("id", "view", "width", "height", "file", "member", "crop", "license", "use", "source_split")
    cells = "".join(f"<td>{escape(str(image[field] if image[field] is not None else ''))}</td>" for field in fields)

    return f"<tr>{cells}</tr>"


def analysis_rows(images: list[dict], analysis: dict) -> str:
    rows = []
    for image in images:
        found = analysis.get(image["id"])
        if found:
            flags = ", ".join(filter(None, found["flags"].split(","))) or "none"
            rows.append(
                f'<tr><td>{escape(image["view"] or "")}</td><td><span class="outcome {found["status"]}">{found["status"]}</span></td>'
                f'<td>{escape(flags)}</td><td>{found["colors"]}</td><td>{found["filled"]}</td><td>{found["soft_edge"]}</td><td>{found["scale"]}x</td></tr>'
            )

    return "".join(rows)


def analysis_table(images: list[dict], analysis: dict, note: str) -> str:
    if not analysis:
        return '<h2>Analysis</h2><p class="muted">Not analyzed yet.</p>'

    header = "".join(f"<th>{name}</th>" for name in ("view", "status", "flags", "colours", "pixels drawn", "soft pixels", "drawn at"))

    return f"""<h2>Analysis</h2>{note}<div class="table"><table><thead><tr>{header}</tr></thead>
<tbody>{analysis_rows(images, analysis)}</tbody></table></div>"""


def character_detail(character: str, images: list[dict], analysis: dict, note: str) -> str:
    if not images:
        return f"<h1>No character {escape(character)}</h1>"

    views = "".join(view_image(image, "large") for image in images)
    header = "".join(f"<th>{name}</th>" for name in ("id", "view", "w", "h", "file", "inside", "crop", "licence", "use", "split"))
    rows = "".join(detail_rows(image) for image in images)
    caption = escape(images[0]["caption"] or "No caption yet.")

    return f"""<h1>{escape(character)}</h1><p>{caption}</p><div class="views">{views}</div>
{analysis_table(images, analysis, note)}
<h2>Records</h2><div class="table"><table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></div>"""
