from conftest import write_export


# Some exports (opengameart-v1) keep no left_out or leaks, and the exports list fell over on them.
def test_an_export_without_a_leak_check_is_still_listed(library, library_client):
    write_export(library.data, "opengameart-v1", {"created_at": "2026-11-24T03:48:36+00:00", "characters": {}})

    exports = library_client.get("/api/exports").json()["exports"]

    assert [export["name"] for export in exports] == ["opengameart-v1", "rotation-test"]
    assert exports[0]["isLeakFree"] is None
    assert exports[0]["leftOut"] == {}


# Character ids hold slashes, and an image id ends in .png only once in its URL.
def test_an_id_with_slashes_and_dots_reaches_its_image(library_client):
    assert library_client.get("/api/images/fake/0/front.png").status_code == 200
    assert library_client.get("/api/characters/fake/0").json()["id"] == "fake/0"
