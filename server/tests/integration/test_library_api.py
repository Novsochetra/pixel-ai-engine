def test_characters_are_listed_with_their_views(library_client):
    reply = library_client.get("/api/characters").json()

    assert reply["imported"] is True
    assert reply["total"] == 3 and reply["pages"] == 1
    assert reply["sources"] == ["fake"]

    knight = reply["characters"][0]
    assert knight["id"] == "fake/0"
    assert [view["label"] for view in knight["views"]] == ["front", "left", "back", "right"]
    assert knight["views"][0]["src"] == "/api/images/fake/0/front.png"


def test_characters_can_be_searched(library_client):
    reply = library_client.get("/api/characters", params={"q": "frog"}).json()

    assert [character["id"] for character in reply["characters"]] == ["fake/1"]


def test_a_bad_page_number_is_refused(library_client):
    assert library_client.get("/api/characters", params={"page": 0}).status_code == 422


def test_one_character_has_its_records_and_analysis(library_client):
    reply = library_client.get("/api/characters/fake/0").json()

    assert reply["caption"] == "a knight with a spear"
    assert reply["analyzed"] is True
    assert reply["images"][0]["license"] == "CC0"
    assert reply["images"][0]["analysis"]["flags"] == ["upscaled"]
    assert reply["group"] is None


def test_a_missing_character_is_not_found(library_client):
    assert library_client.get("/api/characters/fake/9").status_code == 404


def test_flagged_images_are_listed_by_flag(library_client):
    reply = library_client.get("/api/flagged").json()

    assert reply["flag"] == "empty"
    assert reply["flags"][0] == {"name": "empty", "count": 1, "meaning": "nothing drawn", "outcome": "drop"}
    assert [image["id"] for image in reply["images"]] == ["fake/2/front"]


def test_exports_show_counts_and_samples(library_client):
    reply = library_client.get("/api/exports").json()
    export = reply["exports"][0]

    assert export["name"] == "rotation-test"
    assert export["isLeakFree"] is True
    assert export["samples"][0]["views"][0]["src"] == "/api/files/exports/rotation-test/images/front.png"


def test_tryouts_show_each_model_and_its_pictures(library_client):
    run = library_client.get("/api/tryouts").json()["run"]

    assert [model["state"] for model in run["models"]] == ["done", "failed"]
    assert run["groups"][0]["title"] == "pixel art of a knight"
    assert run["groups"][0]["pictures"][0]["src"] == "/api/files/tryouts/run-1/model-a/p00-s0-pixel.png"


def test_images_and_thumbs_come_back_as_png(library_client):
    for path in ("/api/images/fake/0/front.png", "/api/thumbs/fake/0/front.png"):
        reply = library_client.get(path)

        assert reply.headers["content-type"] == "image/png"
        assert reply.content.startswith(b"\x89PNG")

    assert library_client.get("/api/images/fake/9/front.png").status_code == 404


def test_export_and_tryout_pictures_are_served(library_client):
    assert library_client.get("/api/files/exports/rotation-test/images/front.png").status_code == 200
    assert library_client.get("/api/files/tryouts/run-1/model-a/p00-s0-pixel.png").status_code == 200


def test_nothing_outside_the_picture_folders_is_served(library_client):
    refused = (
        "/api/files/exports/%2e%2e/records.sqlite",
        "/api/files/exports/..%2frecords.sqlite",
        "/api/files/tryouts/run-1/results.json",
        "/api/files/raw/fake/0-front.png",
        "/api/files/exports/rotation-test/characters.jsonl",
    )

    for path in refused:
        assert library_client.get(path).status_code == 404, path


def test_no_records_yet_says_so(tmp_path):
    from fastapi.testclient import TestClient
    from pixel_data.dashboard.jobs import Jobs

    from pixel_server.app import create_app

    client = TestClient(create_app(Jobs(tmp_path / "jobs", tmp_path)))

    assert client.get("/api/characters").json()["imported"] is False
    assert client.get("/api/flagged").json()["imported"] is False
    assert client.get("/api/exports").json() == {"exports": []}
    assert client.get("/api/tryouts").json() == {"runs": [], "run": None}
    assert not (tmp_path / "records.sqlite").exists()
