from pathlib import Path

from pixel_data.dashboard import tryouts

from pixel_server.library.urls import file_url


def tryout_list(data: Path, chosen: str) -> dict:
    runs = tryouts.read_runs(data / "tryouts")
    run = next((run for run in runs if run["name"] == chosen), runs[0] if runs else None)

    return {
        "runs": [{"name": run["name"], "createdAt": run["created_at"]} for run in runs],
        "run": run_entry(run) if run else None,
    }


def run_entry(run: dict) -> dict:
    return {
        "name": run["name"],
        "createdAt": run["created_at"],
        "device": run.get("device", ""),
        "models": [model_entry(run, name, result) for name, result in run["models"].items()],
        "groups": create_groups(run) + rotate_groups(run),
    }


def model_entry(run: dict, name: str, result: dict) -> dict:
    if "error" in result:
        state = "failed"
    elif result.get("pending"):
        state = "pending"
    else:
        state = "done"

    return {
        "name": name,
        "repo": run.get("repos", {}).get(name, ""),
        "state": state,
        "error": result.get("error", "")[:300],
        "loadSeconds": result.get("load_seconds"),
        "secondsPerImage": result.get("seconds_per_image"),
    }


def tryout_picture(run: dict, path: str | None, label: str) -> list[dict]:
    return [{"label": label, "src": file_url("tryouts", f"{run['name']}/{path}")}] if path else []


def create_groups(run: dict) -> list[dict]:
    groups = []
    for job in run["create"]:
        pictures = []
        for model in tryouts.finished_models(run):
            for seed in run["seeds"]:
                output = run["models"][model]["create"].get(f"{job['id']}-s{seed}", {})
                pictures += tryout_picture(run, output.get("raw"), f"{model} #{seed}")
                pictures += tryout_picture(run, output.get("pixel"), f"{model} #{seed} 64px")

        groups.append({"title": job["prompt"], "character": None, "pictures": pictures})

    return groups


def rotate_groups(run: dict) -> list[dict]:
    groups = []
    for job in run["rotate"]:
        pictures = tryout_picture(run, job["front"], "front given")
        pictures += tryout_picture(run, job["truth"], f"real {job['view']}")
        for model in tryouts.finished_models(run):
            output = run["models"][model]["rotate"].get(job["id"], {})
            pictures += tryout_picture(run, output.get("pixel"), model)

        title = f"{job['character']} → {job['view']}"
        groups.append({"title": title, "character": job["character"], "pictures": pictures})

    return groups
