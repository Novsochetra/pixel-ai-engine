import json

from PIL import Image

from pixel_training.animate import cycle, jobs_for, pick, run, snap
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
    def animate_all(inputs):
        for prompt, image, seed in inputs:
            calls.append((prompt, image.size, seed))
            frames = []
            for index in range(count):
                frame = Image.new("RGB", image.size, (250, 250, 250))
                frame.paste((40, 40, 190), (160 + index * 4, 80, 352 + index * 4, 480))
                frames.append(frame)
            yield frames

    return animate_all


def test_one_job_per_seed_view_and_action_with_the_subject_in_the_prompt(tmp_path):
    source = character(tmp_path / "knight", seeds=(0, 1))

    jobs = jobs_for(source, [0, 1], ["front", "right", "back"], ["idle", "walk"])

    assert [job.id for job in jobs] == ["s0-front-idle", "s0-front-walk", "s0-right-idle", "s0-right-walk",
                                        "s1-front-idle", "s1-front-walk", "s1-right-idle", "s1-right-walk"]
    assert "a knight" in jobs[0].prompt and "facing right" in jobs[2].prompt and "walk cycle" in jobs[1].prompt
    assert all(job.loops for job in jobs)


def test_the_subject_can_be_given_and_attacks_do_not_loop(tmp_path):
    source = character(tmp_path / "knight")

    jobs = jobs_for(source, [0], ["front"], ["attack"], subject="a knight in grey armour")

    assert "a knight in grey armour" in jobs[0].prompt and "sword" not in jobs[0].prompt
    assert not jobs[0].loops


def test_pick_spreads_the_frames_from_the_first():
    assert pick(list(range(32)), 8) == [0, 4, 8, 12, 16, 20, 24, 28]
    assert pick(list(range(5)), 8) == [0, 1, 2, 3, 4]


def block_at(x):
    sprite = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    sprite.paste((30, 30, 200, 255), (x, 10, x + 10, 60))
    return sprite


def test_a_loop_is_cut_where_the_motion_comes_back_to_the_first_frame():
    # 0, 4, 8, ... 40, then back down: closest to the start again at frame 20, after 10 up and 10 down.
    positions = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 36, 32, 28, 24, 20, 16, 12, 8, 4, 1, 5, 9]
    sprites = [block_at(x) for x in positions]

    assert len(cycle(sprites)) == 20


def test_a_short_clip_is_used_whole():
    assert len(cycle([block_at(0)] * 5)) == 5


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

    rows = run(tmp_path / "out", jobs, fake(calls), 512, keep=4, info={"size": 512})

    assert calls == [(jobs[0].prompt, (512, 512), 0)]
    assert rows[0]["frames"] == 9 and rows[0]["used"] == 8 and rows[0]["kept"] == 4
    assert json.loads((tmp_path / "out" / "animated.json").read_text())["clips"] == rows
    assert Image.open(tmp_path / "out" / "s0-front-walk-sheet.png").size == (4 * 256, 256)
    gif = Image.open(tmp_path / "out" / "s0-front-walk.gif")
    assert gif.n_frames == 8 and gif.size == (256, 256)
    assert (tmp_path / "out" / "s0-front-walk-raw.gif").is_file()


def test_animate_defaults():
    args = parser().parse_args(["animate", "knight"])

    assert (args.actions, args.views, args.size, args.frames, args.keep) == (["idle", "walk"], ["front", "right"], 512, 33, 8)
    assert (args.quant, args.lightning, args.pixel_strength) == ("Q4_K_M", True, 1.0)
    assert parser().parse_args(["animate", "knight", "--no-lightning"]).lightning is False
