from collections import Counter

from pixel_data.gather.importers import IMPORTERS
from pixel_data.records import connect, log_import, replace_source
from pixel_data.sources import Layout, Source, is_gathered


def check_importable(source: Source, layout: Layout) -> None:
    if source.id not in IMPORTERS:
        supported = ", ".join(sorted(IMPORTERS))
        raise SystemExit(f"No importer for {source.id} yet. Importers so far: {supported}.")

    if not is_gathered(source, layout):
        raise SystemExit(f"{source.id} is not downloaded yet. Run `pixel gather {source.id}` first.")


def import_source(source: Source, layout: Layout) -> dict:
    check_importable(source, layout)

    skipped = Counter()
    records = IMPORTERS[source.id](source, layout.source_dir(source), layout.raw, skipped)

    db = connect(layout.records)
    try:
        replace_source(db, source.id, records)
        entry = log_import(db, source.id, dict(skipped))
    finally:
        db.close()

    return entry
