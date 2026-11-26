from pixel_server.same_site import is_same_site


def test_reading_is_always_allowed():
    assert is_same_site("GET", {"sec-fetch-site": "cross-site"})


def test_post_from_this_dashboard():
    assert is_same_site("POST", {"sec-fetch-site": "same-origin"})


def test_post_from_another_site_is_refused():
    assert not is_same_site("POST", {"sec-fetch-site": "cross-site"})


def test_post_from_a_tool_without_browser_headers():
    assert is_same_site("POST", {"host": "127.0.0.1:8780"})


def test_old_browser_post_checks_the_origin():
    assert is_same_site("POST", {"origin": "http://127.0.0.1:8780", "host": "127.0.0.1:8780"})
    assert not is_same_site("POST", {"origin": "https://evil.example", "host": "127.0.0.1:8780"})
