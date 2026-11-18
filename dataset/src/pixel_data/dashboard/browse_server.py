import sqlite3
from contextlib import closing
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import parse_qs, urlparse

from pixel_data.dashboard import browse_pages as pages
from pixel_data.dashboard import browse_queries as queries
from pixel_data.images import load_image, png_bytes
from pixel_data.sources import Layout


def make_handler(layout: Layout) -> type[BaseHTTPRequestHandler]:
    @lru_cache(maxsize=8192)
    def image_bytes(image_id: str) -> bytes | None:
        with open_db(layout) as db:
            row = queries.image_row(db, image_id)

            return png_bytes(load_image(layout.raw, row)) if row else None

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            params = {key: values[0] for key, values in parse_qs(url.query).items()}

            route = THUMBS_ROUTE if url.path.startswith("/thumbs/") else ROUTES.get(url.path)
            if route is None:
                self.send(404, "text/plain", b"Not found")
                return

            route(self, {**params, "path": url.path})

        def send(self, status: int, kind: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def page(self, title: str, body: str) -> None:
            html = pages.layout(title, body, (layout.reports / "dashboard.html").exists())
            self.send(200, "text/html; charset=utf-8", html.encode())

        def log_message(self, *args) -> None:
            pass

    Handler.layout = layout
    Handler.image_bytes = staticmethod(image_bytes)

    return Handler


def open_db(layout: Layout) -> closing:
    db = sqlite3.connect(f"file:{layout.records}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row

    return closing(db)


def home(handler, params: dict) -> None:
    with open_db(handler.layout) as db:
        entries = queries.imports(db)

    handler.page("Imported", pages.home_page(entries))


def page_number(text: str) -> int:
    return max(1, int(text)) if text.isdigit() else 1


def characters(handler, params: dict) -> None:
    filters = queries.Filters(
        params.get("source", ""), params.get("split", ""), params.get("q", ""), page_number(params.get("page", "1"))
    )

    with open_db(handler.layout) as db:
        rows, total = queries.character_page(db, filters)
        sources = [entry["source"] for entry in queries.imports(db)]
        splits = queries.splits(db)

    handler.page("Characters", pages.characters_page(rows, total, filters, sources, splits))


def character(handler, params: dict) -> None:
    name = params.get("id", "")

    with open_db(handler.layout) as db:
        images = queries.character_images(db, name)

    handler.page(name, pages.character_detail(name, images))


def image(handler, params: dict) -> None:
    body = handler.image_bytes(params.get("id", ""))

    if body is None:
        handler.send(404, "text/plain", b"No such image")
        return

    handler.send(200, "image/png", body)


def style(handler, params: dict) -> None:
    css = files("pixel_data.dashboard").joinpath("browse.css").read_bytes()

    handler.send(200, "text/css; charset=utf-8", css)


def downloads(handler, params: dict) -> None:
    page = handler.layout.reports / "dashboard.html"

    if not page.exists():
        handler.send(404, "text/plain", b"Run `pixel dashboard` first.")
        return

    handler.send(200, "text/html; charset=utf-8", page.read_bytes())


def thumbs(handler, params: dict) -> None:
    folder = (handler.layout.reports / "thumbs").resolve()
    target = (handler.layout.reports / params["path"].lstrip("/")).resolve()

    if not target.is_relative_to(folder) or not target.is_file():
        handler.send(404, "text/plain", b"Not found")
        return

    handler.send(200, "image/png", target.read_bytes())


ROUTES = {
    "/": home,
    "/characters": characters,
    "/character": character,
    "/image": image,
    "/style.css": style,
    "/downloads": downloads,
}
THUMBS_ROUTE = thumbs


def serve(layout: Layout, port: int) -> ThreadingHTTPServer:
    if not layout.records.exists():
        raise SystemExit("No records yet. Run `pixel import pac lpc-4view` first.")

    # Only this computer can open it: the data never leaves the machine.
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(layout))
