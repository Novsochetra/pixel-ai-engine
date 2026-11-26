import pytest
from pixel_data.dashboard.studio import Invalid

from pixel_server.create.trash import Busy, folder_name, free_name, in_use, restore_made, trash_made

RUNNING = {"status": "running", "args": ["animate", "/data/generated/knight", "--views", "front"]}


@pytest.mark.parametrize("name", ["20261124-1406-lava-dragon", "knight", "a.b_c-1"])
def test_folder_names_pixel_train_writes(name):
    assert folder_name(name) == name


@pytest.mark.parametrize("name", ["", "../records.sqlite", "a/b", "..", ".hidden", "x..y", None, 3])
def test_anything_that_could_be_a_path_is_refused(name):
    with pytest.raises(Invalid):
        folder_name(name)


def test_a_running_job_that_names_the_folder_uses_it():
    assert in_use("knight", RUNNING)
    assert not in_use("frog", RUNNING)
    assert not in_use("knight", {**RUNNING, "status": "done"})
    assert not in_use("knight", None)


def test_a_second_trashed_copy_gets_its_own_name(tmp_path):
    (tmp_path / "knight").mkdir()
    (tmp_path / "knight-2").mkdir()

    assert free_name(tmp_path, "frog") == "frog"
    assert free_name(tmp_path, "knight") == "knight-3"


def test_trash_and_restore_move_the_folder_back_and_forth(tmp_path):
    (tmp_path / "generated" / "knight").mkdir(parents=True)
    (tmp_path / "generated" / "knight" / "s0-sheet.png").write_bytes(b"png")

    moved = trash_made(tmp_path, "knight", None)

    assert moved == {"folder": "knight", "trashed": "knight"}
    assert not (tmp_path / "generated" / "knight").exists()
    assert (tmp_path / "trash" / "generated" / "knight" / "s0-sheet.png").is_file()

    restore_made(tmp_path, "knight", "knight")

    assert (tmp_path / "generated" / "knight" / "s0-sheet.png").is_file()


def test_a_folder_a_job_uses_stays(tmp_path):
    (tmp_path / "generated" / "knight").mkdir(parents=True)

    with pytest.raises(Busy):
        trash_made(tmp_path, "knight", RUNNING)

    assert (tmp_path / "generated" / "knight").is_dir()


def test_restore_never_overwrites_a_new_folder_of_the_same_name(tmp_path):
    (tmp_path / "generated" / "knight").mkdir(parents=True)
    (tmp_path / "trash" / "generated" / "knight").mkdir(parents=True)

    with pytest.raises(Busy):
        restore_made(tmp_path, "knight", "knight")
