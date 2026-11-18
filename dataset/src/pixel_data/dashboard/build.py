from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pixel_data.dashboard.page import render_page
from pixel_data.dashboard.samples import collect
from pixel_data.dashboard.thumbs import Thumb, save_thumbs
from pixel_data.sources import Layout, Source, folder_size, is_gathered, read_record


@dataclass
class SourceView:
    source: Source
    gathered: bool
    files: int = 0
    bytes: int = 0
    gathered_at: str = ""
    thumbs: list[Thumb] = field(default_factory=list)


def view_source(source: Source, layout: Layout, thumbs_dir: Path) -> SourceView:
    folder = layout.source_dir(source)
    gathered = is_gathered(source, layout)

    if not gathered:
        return SourceView(source, gathered)

    record = read_record(folder) or {}
    files, size = folder_size(folder)

    samples = collect(folder)
    thumbs = save_thumbs(samples, thumbs_dir / source.id)

    return SourceView(source, gathered, files, size, record.get("gathered_at", ""), thumbs)


def build_dashboard(sources: list[Source], layout: Layout) -> Path:
    thumbs_dir = layout.reports / "thumbs"

    views = []
    for source in sources:
        print(f"  reading {source.id}")
        views.append(view_source(source, layout, thumbs_dir))

    page = layout.reports / "dashboard.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(render_page(views, datetime.now().strftime("%Y-%m-%d %H:%M")))

    return page
