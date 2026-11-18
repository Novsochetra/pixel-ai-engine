import json
import tarfile
import zipfile

from helpers import png_bytes, write_parquet

from pixel_data.dashboard.samples import collect


def test_reads_pictures_inside_a_zip(tmp_path):
    with zipfile.ZipFile(tmp_path / "train.zip", "w") as archive:
        for index in range(5):
            archive.writestr(f"images/{index}.png", png_bytes())
        archive.writestr("notes.txt", "not a picture")

    samples = collect(tmp_path, total=3)

    assert len(samples) == 3
    assert all(sample.origin.startswith("train.zip:images/") for sample in samples)


def test_reads_pictures_inside_a_tar(tmp_path):
    for index in range(4):
        (tmp_path / f"{index}.front.png").write_bytes(png_bytes())

    with tarfile.open(tmp_path / "shard.tar", "w") as archive:
        for index in range(4):
            archive.add(tmp_path / f"{index}.front.png", arcname=f"{index}.front.png")

    samples = collect(tmp_path, total=4)

    assert [sample.origin.split(":")[0] for sample in samples] == ["shard.tar"] * 4


def test_reads_pictures_and_captions_from_parquet(tmp_path):
    write_parquet(tmp_path / "train-000.parquet", ["a red knight", "a blue slime"])

    samples = collect(tmp_path, total=2)

    assert [sample.caption for sample in samples] == ["a red knight", "a blue slime"]


def test_ignores_illustrations_beside_the_real_archives(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "banner.png").write_bytes(png_bytes(64))
    with zipfile.ZipFile(tmp_path / "train.zip", "w") as archive:
        archive.writestr("0.png", png_bytes())

    samples = collect(tmp_path)

    assert [sample.origin for sample in samples] == ["train.zip:0.png"]


def test_takes_captions_from_an_image_folder(tmp_path):
    images = tmp_path / "train" / "images"
    images.mkdir(parents=True)
    (images / "cow.png").write_bytes(png_bytes())
    metadata = {"file_name": "images/cow.png", "text": "a cow, pixel art"}
    (tmp_path / "train" / "metadata.jsonl").write_text(json.dumps(metadata))

    samples = collect(tmp_path)

    assert samples[0].caption == "a cow, pixel art"
