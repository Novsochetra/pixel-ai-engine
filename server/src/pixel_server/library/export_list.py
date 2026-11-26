from pathlib import Path

from pixel_data.dashboard import exports

from pixel_server.library.urls import file_url


def export_list(data: Path) -> dict:
    folder = data / "exports"
    summaries = exports.read_exports(folder) if folder.exists() else []

    return {"exports": [export_entry(folder, summary) for summary in summaries]}


def export_entry(folder: Path, summary: dict) -> dict:
    name = summary["name"]
    picks = exports.samples(folder, name)

    return {
        "name": name,
        "createdAt": summary["created_at"],
        "characters": summary["characters"],
        "leftOut": summary.get("left_out", {}),
        "isLeakFree": leak_free(summary),
        "licenses": {source: note.get("license", "") for source, note in summary["sources"].items()},
        "samples": [sample_entry(name, entry) for entries in picks.values() for entry in entries],
    }


# Some exports (opengameart-v1) keep no leak check: None says it was never run.
def leak_free(summary: dict) -> bool | None:
    leaks = summary.get("leaks")

    return None if leaks is None else not any(leaks.values())


def sample_entry(name: str, entry: dict) -> dict:
    return {
        "character": entry["character"],
        "split": entry["split"],
        "views": [
            {"label": view, "src": file_url("exports", f"{name}/{path}")} for view, path in entry["views"].items()
        ],
    }
