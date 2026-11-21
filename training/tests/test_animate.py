import json

from PIL import Image

from pixel_training.animate import jobs_for, pick, run, snap
from pixel_training.cli import parser
from pixel_training.pixelate import palette_of


def character(folder, seeds=(0,), views=("front", "right")):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "generated.json").write_text(json.dumps({"prompt": "a knight"}))
    for seed in seeds:
        for view in views:
            sprite = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            sprite.paste((30, 30, 200, 255), (20, 10, 44, 60))
            sprite.save(folder / f"s{seed}-{view}.png")

    return folder


def fake(calls: list, count: int = 9):
    def animate(prompt, image, seed):
        calls.append((prompt, image.size, seed))
        frames = []
        for index in range(count):
            frame = Image.new("RGB", image.size, (250, 250, 250))
            frame.paste((40, 40, 190), (160 + index * 4, 80, 352 + index * 4, 480))
            frames.append(frame)
        return frames

    return animate


def test_one_job_per_seed_view_and_action_with_the_subject_in_the_prompt(tmp_path):
    source = character(tmp_path / "knight", seeds=(0, 1))

    jobs = jobs_for(source, [0, 1], ["front", "right", "back"], ["idle", "walk"])

    assert [job.id for job in jobs] == ["s0-front-idle", "s0-front-walk", "s0-right-idle", "s0-right-walk",
                                        "s1-front-idle", "s1-front-walk", "s1-right-idle", "s1-right-walk"]
    assert "a knight" in jobs[0].prompt and "facing right" in jobs[2].prompt and "walking" in jobs[1].prompt


def test_pick_skips_the_input_frame_and_spreads_the_rest():
    assert pick(list(range(33)), 8) == [1, 5, 9, 13, 17, 21, 25, 29]
    assert pick(list(range(5)), 8) == [1, 2, 3, 4]


def test_a_frame_snaps_to_a_sprite_in_the_input_colours():
    sprite = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    sprite.paste((30, 30, 200, 255), (20, 10, 44, 60))
    frame = Image.new("RGB", (512, 512), (245, 248, 250))
    frame.paste((50, 45, 180), (160, 80, 352, 480))

    small = snap(frame, palette_of(sprite))

    assert small.size == (64, 64)
    assert small.getpixel((0, 0))[3] == 0
    assert small.getpixel((32, 30)) == (30, 30, 200, 255)


def test_run_writes_the_raw_gif_the_sprite_gif_and_the_sheet(tmp_path):
    source = character(tmp_path / "knight")
    jobs = jobs_for(source, [0], ["front"], ["walk"])
    calls = []

    rows = run(tmp_path / "out", jobs, fake(calls), 512, keep=4)

    assert calls == [(jobs[0].prompt, (512, 512), 0)]
    assert rows[0]["frames"] == 9 and rows[0]["kept"] == 4
    assert Image.open(tmp_path / "out" / "s0-front-walk-sheet.png").size == (4 * 256, 256)
    gif = Image.open(tmp_path / "out" / "s0-front-walk.gif")
    assert gif.n_frames == 9 and gif.size == (256, 256)
    assert (tmp_path / "out" / "s0-front-walk-raw.gif").is_file()


def test_animate_defaults():
    args = parser().parse_args(["animate", "knight"])

    assert (args.actions, args.views, args.size, args.frames, args.keep) == (["idle", "walk"], ["front", "right"], 512, 33, 8)
    assert (args.quant, args.lightning, args.pixel_strength) == ("Q4_K_M", True, 1.0)
    assert parser().parse_args(["animate", "knight", "--no-lightning"]).lightning is False
