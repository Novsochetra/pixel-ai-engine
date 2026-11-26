import json

from conftest import save_png

from pixel_server.create.generated_list import generated_list


# The first generations (before 2026-11-24) kept no sprite size or facing: they were 64 px fronts.
def test_an_early_generation_reads_as_a_64_px_front(tmp_path):
    folder = tmp_path / "generated" / "20261121-1146-a-frog-wizard-with-a-staff"
    save_png(folder / "s0-sheet.png")
    info = {"created_at": "2026-11-21T04:50:09+00:00", "prompt": "a frog wizard with a staff", "seeds": [0, 1],
            "front_model": "flux2-klein-4b", "lora": "../dataset/data/runs/rotate-v2/final",
            "turn_model": "flux2-klein-4b", "size": 256}
    (folder / "generated.json").write_text(json.dumps(info))

    entry = generated_list(tmp_path)["items"][0]

    assert entry["sprite"] == 64
    assert entry["facing"] == "front"
    assert entry["turnWith"] == "rotate-v2 · final"
