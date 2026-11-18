import json

import pytest
from helpers import fake_lpc_4view, fake_pac
from PIL import Image

from pixel_data.analyze.run import analyze
from pixel_data.export.fix import fixed
from pixel_data.export.run import export
from pixel_data.export.select import reason_to_leave_out
from pixel_data.export.split import assign_splits, bucket
from pixel_data.gather.importer import import_source
from pixel_data.sources import Layout, Source


def test_half_transparent_pixels_become_solid_or_clear():
    image = Image.new("RGBA", (4, 1))
    for x, alpha in enumerate((0, 100, 128, 255)):
        image.putpixel((x, 0), (10, 20, 30, alpha))

    result = fixed(image, ["soft-edges"], 1)
    alphas = [result.getpixel((x, 0))[3] for x in range(4)]

    assert alphas == [0, 0, 255, 255]


def test_art_drawn_at_double_size_is_shrunk():
    image = Image.new("RGBA", (64, 64), (1, 2, 3, 255))

    assert fixed(image, ["upscaled"], 2).size == (32, 32)
    assert fixed(image, [], 2).size == (64, 64)


def character(name: str, group: str, source_split: str = "train", use: str = "train") -> dict:
    return {"character": name, "group": group, "source_split": source_split, "use": use}


def test_a_group_always_lands_in_one_split():
    characters = [character(f"c{index}", f"g{index % 7}") for index in range(70)]

    splits = assign_splits(characters)

    for group in {item["group"] for item in characters}:
        assert len({splits[item["character"]] for item in characters if item["group"] == group}) == 1


def test_a_held_out_member_pulls_its_whole_group_into_test():
    characters = [character("a", "g"), character("b", "g", source_split="test"), character("c", "h", use="eval")]

    assert assign_splits(characters) == {"a": "test", "b": "test", "c": "test"}


def test_the_split_of_a_group_never_changes():
    assert [bucket(f"group-{index}") for index in range(50)] == [bucket(f"group-{index}") for index in range(50)]

    shares = [bucket(f"group-{index}") for index in range(4000)]
    assert 0.86 < shares.count("train") / len(shares) < 0.94


def view(name: str, status: str) -> dict:
    return {"view": name, "status": status}


def test_a_character_needs_all_four_views_and_none_dropped():
    full = [view(name, "ok") for name in ("front", "left", "back", "right")]

    assert reason_to_leave_out(full, {"ok", "fix"}) is None
    assert reason_to_leave_out(full[:3], {"ok", "fix"}) == "missing a view"
    assert reason_to_leave_out([*full[:3], view("right", "drop")], {"ok", "fix"}) == "a view is dropped"
    assert reason_to_leave_out([*full[:3], view("right", "check")], {"ok", "fix"}) == "a view needs checking"
    assert reason_to_leave_out([*full[:3], view("right", "check")], {"ok", "fix", "check"}) is None


@pytest.fixture
def exported(tmp_path):
    layout = Layout(tmp_path)
    sources = [fake_pac(layout), fake_lpc_4view(layout)]
    for source in sources:
        import_source(source, layout)
    analyze(layout, [])

    summary = export(layout, sources, "rotation-test", include_check=True, experimental=False)

    return layout, summary


def test_export_writes_every_view_of_every_character(exported):
    layout, summary = exported
    folder = layout.data / "exports" / "rotation-test"

    entries = [json.loads(line) for line in (folder / "characters.jsonl").read_text().splitlines()]

    assert len(entries) == sum(sum(counts.values()) for counts in summary["characters"].values())
    for entry in entries:
        assert set(entry["views"]) == {"front", "left", "back", "right"}
        assert all((folder / path).is_file() for path in entry["views"].values())


def test_export_drops_copies_and_reports_no_leaks(exported):
    _, summary = exported

    assert summary["left_out"] == {"a view is dropped": 1}
    assert summary["leaks"] == {"groups_in_two_splits": 0, "pictures_in_two_splits": 0}


def test_experimental_sources_stay_out_unless_asked(tmp_path):
    layout = Layout(tmp_path)
    pac = fake_pac(layout)
    import_source(pac, layout)
    analyze(layout, [])
    risky = Source(**{**pac.__dict__, "use": "experimental"})

    summary = export(layout, [risky], "clean", include_check=True, experimental=False)

    assert summary["characters"] == {}


def test_an_export_name_cannot_leave_the_exports_folder(tmp_path):
    with pytest.raises(SystemExit, match="lowercase letters"):
        export(Layout(tmp_path), [], "../escape", include_check=False, experimental=False)
