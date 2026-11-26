from urllib.parse import urlparse

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
SAME_SITE = {"same-origin", "none"}


# Another site open in the browser could post to 127.0.0.1 and start a training run that fills the Mac.
def is_same_site(method: str, headers: dict[str, str]) -> bool:
    if method.upper() in SAFE_METHODS:
        return True

    fetch_site = headers.get("sec-fetch-site")
    if fetch_site:
        return fetch_site in SAME_SITE

    origin = headers.get("origin")

    return origin is None or urlparse(origin).netloc == headers.get("host")
