from pathlib import Path

from pixel_data.dashboard import studio

from pixel_server.create.form_options import choices

# train_job, resume_job and tryout_job check these; the forms show the same limits before they send.
MOST_STEPS = 50000
CHARACTERS = {"min": 1, "max": 20, "default": 4}
DEFAULTS = {
    "task": "rotate",
    "model": "flux2-klein-base-4b",
    "size": "256",
    "steps": 2000,
    "tryoutModel": "flux2-klein-4b",
    "addSteps": 500,
}


def training_options(data: Path) -> dict:
    return {
        "tasks": choices(studio.TASKS),
        "models": choices(studio.MODELS),
        "sizes": [{"value": str(size), "label": f"{size} px"} for size in studio.SIZES],
        "exports": [export_entry(data, name) for name in studio.exports(data)],
        "namePattern": studio.NAME.pattern,
        "mostSteps": MOST_STEPS,
        "characters": CHARACTERS,
        "defaults": DEFAULTS,
    }


def export_entry(data: Path, name: str) -> dict:
    sources = studio.read_json(data / "exports" / name / "export.json").get("sources", {})

    return {"name": name, "sources": [source_entry(source, sources[source]) for source in sorted(sources)]}


def source_entry(name: str, info) -> dict:
    info = info if isinstance(info, dict) else {}

    return {"name": name, "licence": info.get("license", ""), "use": info.get("use", "")}
