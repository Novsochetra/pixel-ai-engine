from pixel_server.library.characters import split_flags
from pixel_server.library.export_list import leak_free
from pixel_server.library.pictures import file_under
from pixel_server.library.tryout_list import model_entry, rotate_groups
from pixel_server.library.urls import file_url, image_url, picture


def test_urls_keep_the_slashes_of_an_id_and_quote_the_rest():
    assert image_url("pac/train/0/front") == "/api/images/pac/train/0/front.png"
    assert image_url("moss-64/a b#c") == "/api/images/moss-64/a%20b%23c.png"
    assert file_url("exports", "v1/images/front.png") == "/api/files/exports/v1/images/front.png"


def test_a_picture_has_a_full_size_and_a_thumb():
    assert picture("fake/0/front", "front") == {
        "id": "fake/0/front",
        "label": "front",
        "src": "/api/images/fake/0/front.png",
        "thumb": "/api/thumbs/fake/0/front.png",
    }


def test_flags_are_split_without_empty_names():
    assert split_flags("") == []
    assert split_flags("duplicate,touches-edge") == ["duplicate", "touches-edge"]


def test_leaks_are_free_only_when_every_count_is_zero():
    assert leak_free({"leaks": {"groups_in_two_splits": 0, "pictures_in_two_splits": 0}}) is True
    assert leak_free({"leaks": {"groups_in_two_splits": 2}}) is False
    assert leak_free({}) is None


def test_files_are_found_only_as_pictures_inside_their_folder(tmp_path):
    picture_file = tmp_path / "exports" / "v1" / "front.png"
    picture_file.parent.mkdir(parents=True)
    picture_file.write_bytes(b"png")
    (tmp_path / "exports" / "v1" / "export.json").write_text("{}")
    (tmp_path / "secret.png").write_bytes(b"png")

    assert file_under(tmp_path, "exports", "v1/front.png") == picture_file.resolve()
    assert file_under(tmp_path, "exports", "v1/export.json") is None
    assert file_under(tmp_path, "exports", "../secret.png") is None
    assert file_under(tmp_path, "exports", "/etc/hosts") is None
    assert file_under(tmp_path, "raw", "front.png") is None


def test_a_model_is_done_failed_or_not_run_yet():
    run = {"repos": {"a": "someone/a"}}

    assert model_entry(run, "a", {"load_seconds": 3, "seconds_per_image": 1.5})["state"] == "done"
    assert model_entry(run, "a", {"error": "x" * 400})["error"] == "x" * 300
    assert model_entry(run, "b", {"pending": True}) == {
        "name": "b",
        "repo": "",
        "state": "pending",
        "error": "",
        "loadSeconds": None,
        "secondsPerImage": None,
    }


def test_rotate_groups_show_the_given_front_the_truth_and_each_model():
    run = {
        "name": "run-1",
        "rotate": [{"id": "r0", "character": "pac/0", "view": "left", "front": "f.png", "truth": "t.png"}],
        "models": {"a": {"create": {}, "rotate": {"r0": {"pixel": "a/r0.png"}}}, "b": {"error": "gated"}},
    }

    group = rotate_groups(run)[0]

    assert group["title"] == "pac/0 → left"
    assert [picture["label"] for picture in group["pictures"]] == ["front given", "real left", "a"]
