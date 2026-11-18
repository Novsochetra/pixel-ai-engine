import tarfile

from helpers import add_to_tar, fake_lpc_4view, fake_pac, png_bytes
from PIL import Image

from pixel_data.analyze.measure import measure
from pixel_data.analyze.rules import image_flags, status_of
from pixel_data.analyze.run import analyze
from pixel_data.gather.importer import import_source
from pixel_data.records import connect
from pixel_data.sources import Layout


def sprite(size: int = 64) -> Image.Image:
    # Odd sizes and offsets, so the block does not line up with a 2x grid by chance.
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    block = (size // 3 | 1, size // 2 - 1)
    image.paste(Image.new("RGBA", block, (200, 50, 50, 255)), (size // 3 | 1, size // 2 + 1))

    return image


def test_a_clean_sprite_raises_no_flags():
    measures = measure(sprite())

    assert (measures.filled, measures.colors, measures.soft_edge, measures.scale) == (21 * 31, 1, 0, 1)
    assert image_flags(measures) == []


def test_nothing_drawn_is_only_empty():
    assert image_flags(measure(Image.new("RGBA", (64, 64)))) == ["empty"]


def test_feet_on_the_bottom_row_are_not_cut_off():
    image = Image.new("RGBA", (64, 64))
    image.paste(Image.new("RGBA", (10, 20), (9, 9, 9, 255)), (20, 44))
    assert "touches-edge" not in image_flags(measure(image))

    image.paste(Image.new("RGBA", (10, 20), (9, 9, 9, 255)), (0, 10))
    assert "touches-edge" in image_flags(measure(image))


def test_half_transparent_pixels_are_counted():
    image = sprite()
    image.putpixel((21, 33), (200, 50, 50, 120))

    measures = measure(image)

    assert measures.soft_edge == 1
    assert image_flags(measures) == ["soft-edges"]


def test_art_drawn_at_double_size_is_found():
    small = sprite(32)
    doubled = small.resize((64, 64), Image.NEAREST)

    assert measure(doubled).scale == 2
    assert "upscaled" in image_flags(measure(doubled))


def test_hidden_colours_behind_transparency_do_not_change_the_hash():
    one = sprite()
    other = sprite()
    other.putpixel((0, 0), (255, 255, 255, 0))

    assert measure(one).pixel_hash == measure(other).pixel_hash


def test_the_worst_flag_decides_the_status():
    assert status_of([]) == "ok"
    assert status_of(["soft-edges", "near-duplicate"]) == "fix"
    assert status_of(["soft-edges", "duplicate"]) == "drop"


def add_copy_of_character_one(layout: Layout) -> None:
    tar = layout.raw / "pac" / "pac-train-000001.tar"

    with tarfile.open(tar, "w") as archive:
        for shade, view in enumerate(("back", "left", "front", "right")):
            add_to_tar(archive, f"7.{view}.png", png_bytes(64, (shade * 60, 90, 10, 255)))


def analyzed_layout(tmp_path) -> Layout:
    layout = Layout(tmp_path)
    pac = fake_pac(layout)
    add_copy_of_character_one(layout)
    import_source(pac, layout)
    import_source(fake_lpc_4view(layout), layout)
    analyze(layout, [])

    return layout


def test_an_exact_copy_of_a_character_is_dropped_and_points_at_the_original(tmp_path):
    layout = analyzed_layout(tmp_path)
    db = connect(layout.records)

    copy = db.execute("SELECT * FROM character_groups WHERE character = 'pac/train/7'").fetchone()
    statuses = {row[0] for row in db.execute("SELECT status FROM analysis WHERE id LIKE 'pac/train/7/%'")}

    assert copy["copy_of"] == "pac/train/1"
    assert statuses == {"drop"}


def test_analyze_reports_every_source(tmp_path):
    layout = Layout(tmp_path)
    import_source(fake_pac(layout), layout)
    import_source(fake_lpc_4view(layout), layout)

    result = analyze(layout, [])

    assert set(result["summary"]) == {"pac", "lpc-4view"}
    statuses = {key: count for key, count in result["summary"]["lpc-4view"].items() if key.startswith("status:")}
    assert sum(statuses.values()) == 4
