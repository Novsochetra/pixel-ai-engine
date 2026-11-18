import threading
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest
from helpers import fake_lpc_4view, fake_pac

from pixel_data.analyze.run import analyze
from pixel_data.dashboard.browse_server import serve
from pixel_data.export.run import export
from pixel_data.gather.importer import import_source
from pixel_data.sources import Layout


def start(layout: Layout):
    server = serve(layout, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    return server, f"http://127.0.0.1:{server.server_address[1]}"


@pytest.fixture
def analyzed_browser(tmp_path):
    layout = Layout(tmp_path)
    import_source(fake_pac(layout), layout)
    analyze(layout, [])

    server, url = start(layout)
    yield url

    server.shutdown()
    server.server_close()


@pytest.fixture
def browser(tmp_path):
    layout = Layout(tmp_path)
    import_source(fake_pac(layout), layout)
    import_source(fake_lpc_4view(layout), layout)
    (layout.reports / "thumbs").mkdir(parents=True)

    server = serve(layout, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    yield f"http://127.0.0.1:{server.server_address[1]}"

    server.shutdown()
    server.server_close()


def fetch(url: str) -> tuple[int, str, bytes]:
    try:
        with urlopen(url) as response:
            return response.status, response.headers["Content-Type"], response.read()
    except HTTPError as error:
        return error.code, error.headers["Content-Type"], error.read()


def test_home_lists_each_imported_source(browser):
    status, _, body = fetch(browser + "/")

    assert status == 200
    assert b"3 characters" in body and b"1 characters" in body


def test_characters_can_be_filtered_by_source_split_and_search(browser):
    _, _, every = fetch(browser + "/characters")
    _, _, tests = fetch(browser + "/characters?source=pac&split=test")
    _, _, spear = fetch(browser + "/characters?q=spear")

    assert b"4 characters" in every
    assert b"1 characters" in tests and b"pac/test/0" in tests
    assert b"lpc-4view/char_00000" in spear and b"pac/train/0" not in spear


def test_a_character_page_shows_every_view_in_order(browser):
    _, _, body = fetch(browser + "/character?id=lpc-4view/char_00000")
    html = body.decode()

    positions = [html.index(f'alt="{view}"') for view in ("front", "left", "back", "right")]
    assert positions == sorted(positions)


def test_images_come_back_as_png(browser):
    status, kind, body = fetch(browser + "/image?id=pac/train/0/front")

    assert (status, kind) == (200, "image/png")
    assert body.startswith(b"\x89PNG")


def test_nothing_outside_the_thumbs_folder_is_served(browser):
    status, _, _ = fetch(browser + "/thumbs/../records.sqlite")

    assert status == 404


def test_a_bad_page_number_shows_the_first_page(browser):
    status, _, body = fetch(browser + "/characters?page=abc")

    assert status == 200 and b"Page 1 of 1" in body


def test_browse_needs_records_first(tmp_path):
    with pytest.raises(SystemExit, match="pixel import"):
        serve(Layout(tmp_path), 0)


def test_flagged_asks_for_analysis_until_it_has_run(browser):
    _, _, body = fetch(browser + "/flagged")

    assert b"Not analyzed yet" in body


def test_flagged_lists_images_by_flag(analyzed_browser):
    _, _, body = fetch(analyzed_browser + "/flagged?flag=duplicate")

    assert b"duplicate <b>4</b>" in body
    assert b"pac/train/0/front" in body


def test_a_copied_character_names_its_original(analyzed_browser):
    _, _, body = fetch(analyzed_browser + "/character?id=pac/train/0")

    assert b"Exact copy of" in body and b"pac/test/0" in body


def test_home_shows_statuses_once_analyzed(analyzed_browser):
    _, _, body = fetch(analyzed_browser + "/")

    assert b'class="outcome drop"' in body


@pytest.fixture
def exported_browser(tmp_path):
    layout = Layout(tmp_path)
    pac = fake_pac(layout)
    import_source(pac, layout)
    analyze(layout, [])
    export(layout, [pac], "rotation-test", include_check=True, experimental=False)

    server, url = start(layout)
    yield url

    server.shutdown()
    server.server_close()


def test_exports_asks_for_an_export_until_one_exists(analyzed_browser):
    _, _, body = fetch(analyzed_browser + "/exports")

    assert b"No exports yet" in body


def test_exports_shows_counts_leak_check_and_samples(exported_browser):
    _, _, body = fetch(exported_browser + "/exports")

    assert b"rotation-test" in body and b"Leak check" in body
    assert b"/exports/rotation-test/images/" in body


def test_exported_pictures_are_served_but_nothing_else(exported_browser):
    _, _, page = fetch(exported_browser + "/exports")
    picture = page.decode().split('src="/exports/rotation-test/')[1].split('"')[0]

    assert fetch(exported_browser + f"/exports/rotation-test/{picture}")[0] == 200
    assert fetch(exported_browser + "/exports/rotation-test/characters.jsonl")[0] == 404
    assert fetch(exported_browser + "/exports/%2e%2e/records.sqlite")[0] == 404
