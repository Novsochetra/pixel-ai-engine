import json
from pathlib import Path

from PIL import Image

from pixel_training.tryout import Plan, create_jobs, rotate_jobs, run_model, write_results

PROMPTS = {
    "create": {"template": "pixel art of {subject}", "subjects": ["a knight", "a slime"]},
    "rotate": {"left": "turn left", "back": "turn around"},
}


def fake_export(folder: Path) -> Path:
    for split, name in (("train", "a"), ("test", "b"), ("test", "c")):
        for view in ("front", "left", "back", "right"):
            path = folder / "images" / name / f"{view}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGBA", (64, 64), (9, 9, 9, 255)).save(path)

    lines = [
        json.dumps({"character": f"src/{name}", "split": split,
                    "views": {view: f"images/{name}/{view}.png" for view in ("front", "left", "back", "right")}})
        for split, name in (("train", "a"), ("test", "b"), ("test", "c"))
    ]
    (folder / "characters.jsonl").write_text("\n".join(lines))

    return folder


def fake_generate(calls: list):
    def generate(prompt: str, image, seed: int) -> Image.Image:
        calls.append((prompt, image is not None, seed))
        return Image.new("RGB", (1024, 1024), (255, 255, 255))

    return generate


def test_create_jobs_fill_the_template():
    jobs = create_jobs(PROMPTS)

    assert [job["prompt"] for job in jobs] == ["pixel art of a knight", "pixel art of a slime"]


def test_rotation_uses_only_test_characters(tmp_path):
    jobs = rotate_jobs(fake_export(tmp_path), PROMPTS, count=5)

    assert {job["character"] for job in jobs} == {"src/b", "src/c"}
    assert {job["view"] for job in jobs} == {"left", "back"}


def test_a_model_run_saves_raw_and_pixel_pictures(tmp_path):
    plan = Plan(tmp_path / "run", create_jobs(PROMPTS), rotate_jobs(fake_export(tmp_path / "export"), PROMPTS, 1), [0, 1])
    calls = []

    result = run_model(plan, "fake", lambda: fake_generate(calls))

    assert len(calls) == 2 * 2 + 2
    assert sum(1 for _, has_image, _ in calls if has_image) == 2
    assert set(result["create"]) == {"p00-s0", "p00-s1", "p01-s0", "p01-s1"}
    assert Image.open(plan.folder / result["create"]["p00-s0"]["pixel"]).size == (64, 64)


def test_a_model_that_cannot_load_is_reported_not_raised(tmp_path):
    plan = Plan(tmp_path, create_jobs(PROMPTS), [], [0])

    def refuse():
        raise OSError("401 Client Error: gated repo")

    assert run_model(plan, "locked", refuse) == {"error": "OSError: 401 Client Error: gated repo"}


def test_results_list_prompts_references_and_models(tmp_path):
    plan = Plan(tmp_path / "run", create_jobs(PROMPTS), rotate_jobs(fake_export(tmp_path / "export"), PROMPTS, 1), [0])
    result = run_model(plan, "fake", lambda: fake_generate([]))

    path = write_results(plan, "run", {"fake": result}, {"device": "cpu"})
    saved = json.loads(path.read_text())

    assert [item["id"] for item in saved["create"]] == ["p00", "p01"]
    assert all((plan.folder / row["truth"]).is_file() for row in saved["rotate"])
    assert saved["models"]["fake"]["seconds_per_image"] >= 0
