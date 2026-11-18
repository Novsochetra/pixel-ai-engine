from html import escape
from importlib.resources import files

TASKS = ("create", "rotate", "animate", "landscape")
USES = ("train", "eval", "experimental")


def human_size(byte_count: int) -> str:
    size = float(byte_count)

    for unit in ("B", "KB", "MB", "GB"):
        if size < 1000:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1000

    return f"{size:.1f} TB"


def source_link(source) -> str:
    if source.kind == "huggingface":
        return f"https://huggingface.co/datasets/{source.repo}"

    if source.kind == "git":
        return source.repo.removesuffix(".git")

    return source.links[0] if source.links else ""


def thumb_title(thumb) -> str:
    colors = f"{thumb.colors} colours" if thumb.colors else "4096+ colours"
    parts = [f"{thumb.width}×{thumb.height}", colors, thumb.caption, thumb.origin]

    return " · ".join(part for part in parts if part)


def render_thumb(view, thumb) -> str:
    src = f"thumbs/{escape(view.source.id)}/{thumb.file}"
    title = escape(thumb_title(thumb))

    return f'<a class="thumb" href="{src}" target="_blank" title="{title}"><img src="{src}" alt="{title}" loading="lazy"></a>'


def render_status(view) -> str:
    if view.gathered:
        return '<span class="status ok">downloaded</span>'

    if view.source.kind == "manual":
        return '<span class="status wait">download by hand</span>'

    return '<span class="status missing">not downloaded</span>'


def render_meta(view) -> str:
    source = view.source
    items = [f"<dt>Licence</dt><dd>{escape(source.license)}</dd>"]

    if view.gathered:
        items.append(f"<dt>On disk</dt><dd>{view.files:,} files · {human_size(view.bytes)}</dd>")

    if source.revision:
        items.append(f"<dt>Version</dt><dd><code>{escape(source.revision[:10])}</code></dd>")

    return f'<dl class="meta">{"".join(items)}</dl>'


def render_samples(view) -> str:
    if view.thumbs:
        return f'<div class="thumbs">{"".join(render_thumb(view, thumb) for thumb in view.thumbs)}</div>'

    if view.gathered:
        return '<p class="empty">No images found to preview yet.</p>'

    command = f"pixel gather {escape(view.source.id)}"
    if view.source.kind == "manual":
        return f'<p class="empty">Run <code>{command}</code> for the links and its folder, put the files there, then <code>pixel dashboard</code>.</p>'

    return f'<p class="empty">Run <code>{command}</code></p>'


def render_card(view) -> str:
    source = view.source
    tasks = "".join(f'<span class="tag">{escape(task)}</span>' for task in source.tasks)
    link = source_link(source)
    title = f'<a href="{escape(link)}" target="_blank">{escape(source.id)}</a>' if link else escape(source.id)
    state = "gathered" if view.gathered else "missing"

    return f"""
<article class="card" data-use="{escape(source.use)}" data-tasks="{escape(' '.join(source.tasks))}" data-state="{state}">
  <header>
    <h2>{title}</h2>
    <span class="use use-{escape(source.use)}">{escape(source.use)}</span>
    {render_status(view)}
  </header>
  <div class="tags">{tasks}</div>
  <p class="notes">{escape(source.notes)}</p>
  {render_meta(view)}
  {render_samples(view)}
</article>"""


def render_summary(views) -> str:
    gathered = [view for view in views if view.gathered]
    total = sum(view.bytes for view in gathered)
    experimental = sum(1 for view in views if view.source.is_experimental)

    tiles = [
        ("Sources", f"{len(views)}"),
        ("Downloaded", f"{len(gathered)} of {len(views)}"),
        ("On disk", human_size(total)),
        ("Experimental only", f"{experimental}"),
    ]

    return "".join(f'<div class="tile"><span>{label}</span><strong>{value}</strong></div>' for label, value in tiles)


def render_filters() -> str:
    chips = [("all", "All")] + [(f"use:{use}", use) for use in USES] + [(f"task:{task}", task) for task in TASKS]
    chips.append(("state:missing", "not downloaded"))

    return "".join(
        f'<button class="chip{" on" if key == "all" else ""}" data-filter="{key}">{escape(label)}</button>'
        for key, label in chips
    )


def render_page(views, generated_at: str) -> str:
    template = files("pixel_data.dashboard").joinpath("template.html").read_text()
    cards = "".join(render_card(view) for view in views)

    return (
        template.replace("{{generated_at}}", escape(generated_at))
        .replace("{{summary}}", render_summary(views))
        .replace("{{filters}}", render_filters())
        .replace("{{cards}}", cards)
    )
