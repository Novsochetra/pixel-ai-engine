import json
import sqlite3
import threading
from contextlib import closing
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from pixel_data.dashboard import browse_pages as pages
from pixel_data.dashboard import browse_queries as queries
from pixel_data.dashboard import exports, flagged, studio, tryouts
from pixel_data.dashboard.jobs import Jobs
from pixel_data.images import load_image, png_bytes
from pixel_data.records import connect
from pixel_data.sources import Layout


def make_handler(layout: Layout, jobs: Jobs) -> type[BaseHTTPRequestHandler]:
    @lru_cache(maxsize=8192)
    def image_bytes(image_id: str) -> bytes | None:
        with open_db(layout) as db:
            row = queries.image_row(db, image_id)

            return png_bytes(load_image(layout.raw, row)) if row else None

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            params = {key: values[0] for key, values in parse_qs(url.query).items()}

            route = file_route(url.path) or ROUTES.get(url.path)
            if route is None:
                self.send(404, "text/plain", b"Not found")
                return

            route(self, {**params, "path": unquote(url.path)})

        def do_POST(self):
            # Only pages of this dashboard may start jobs: another site open in the browser could
            # otherwise post a form to 127.0.0.1 and start a training run.
            if not self.same_site():
                self.send(403, "text/plain", b"Forbidden")
                return

            url = urlparse(self.path)
            route = POST_ROUTES.get(url.path)
            if route is None:
                self.send(404, "text/plain", b"Not found")
                return

            length = min(int(self.headers.get("Content-Length") or 0), 64_000)
            fields = parse_qs(self.rfile.read(length).decode("utf-8", "replace"), keep_blank_values=True)
            form = {key: values[0] for key, values in fields.items()}
            form["sources_list"] = fields.get("sources", [])
            route(self, form)

        def same_site(self) -> bool:
            port = self.server.server_address[1]
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            origin = self.headers.get("Origin")
            if self.headers.get("Host") not in hosts:
                return False

            return origin is None or urlparse(origin).netloc in hosts

        def redirect(self, where: str) -> None:
            self.send_response(303)
            self.send_header("Location", where)
            self.send_header("Content-Length", "0")
            self.end_headers()

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
    Handler.jobs = jobs
    Handler.image_bytes = staticmethod(image_bytes)

    return Handler


def open_db(layout: Layout) -> closing:
    db = sqlite3.connect(f"file:{layout.records}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row

    return closing(db)


def home(handler, params: dict) -> None:
    with open_db(handler.layout) as db:
        entries = queries.imports(db)
        statuses = flagged.status_counts(db) if flagged.analyzed(db) else {}

    handler.page("Imported", pages.home_page(entries, statuses))


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
        analysis, group = flagged.character_analysis(db, name)
        note = flagged.group_note(db, group)

    handler.page(name, pages.character_detail(name, images, analysis, note))


def flagged_images(handler, params: dict) -> None:
    with open_db(handler.layout) as db:
        sources = [entry["source"] for entry in queries.imports(db)]
        body = flagged.flagged_page(
            db, params.get("flag", ""), params.get("source", ""), page_number(params.get("page", "1")), sources
        )

    handler.page("Flagged", body)


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


def send_png_under(handler, folder: Path, relative: str) -> None:
    target = (folder / relative).resolve()

    if not target.is_relative_to(folder.resolve()) or not target.is_file() or target.suffix != ".png":
        handler.send(404, "text/plain", b"Not found")
        return

    handler.send(200, "image/png", target.read_bytes())


def thumbs(handler, params: dict) -> None:
    send_png_under(handler, handler.layout.reports / "thumbs", params["path"].removeprefix("/thumbs/"))


def export_file(handler, params: dict) -> None:
    send_png_under(handler, handler.layout.data / "exports", params["path"].removeprefix("/exports/"))


def tryout_file(handler, params: dict) -> None:
    send_png_under(handler, handler.layout.data / "tryouts", params["path"].removeprefix("/tryouts/"))


def tryout_list(handler, params: dict) -> None:
    handler.page("Try-outs", tryouts.tryouts_page(handler.layout.data / "tryouts", params.get("run", "")))


def export_list(handler, params: dict) -> None:
    handler.page("Exports", exports.exports_page(handler.layout.data / "exports"))



def generated_file(handler, params: dict) -> None:
    send_png_under(handler, handler.layout.data / "generated", params["path"].removeprefix("/generated/"))


def latest_job(handler) -> tuple[dict | None, str]:
    job = handler.jobs.latest()

    return job, handler.jobs.log(job["id"]) if job else ""


def generate_page(handler, params: dict, message: str = "", status: int = 200) -> None:
    job, log = latest_job(handler)
    body = studio.generate_page(handler.layout.data, job, log, params, message)
    html = pages.layout("Generate", body, (handler.layout.reports / "dashboard.html").exists())
    handler.send(status, "text/html; charset=utf-8", html.encode())


def training_page(handler, params: dict, message: str = "", status: int = 200) -> None:
    job, log = latest_job(handler)
    body = studio.training_page(handler.layout.data, job, log, params, message)
    html = pages.layout("Training", body, (handler.layout.reports / "dashboard.html").exists())
    handler.send(status, "text/html; charset=utf-8", html.encode())


def current_job(handler, params: dict) -> None:
    job, log = latest_job(handler)
    handler.send(200, "application/json", json.dumps({"job": job, "log": log}).encode())


def start_job(make, page, where: str):
    """A form route: check the form, start the job, and go back to the page; or show what is wrong."""
    def route(handler, form: dict) -> None:
        try:
            title, args = make(handler.layout.data, form)
            handler.jobs.start(where.strip("/"), title, args)
        except (studio.Invalid, RuntimeError) as error:
            page(handler, form, str(error), 400)
            return

        handler.redirect(where)

    return route


def stop_job(handler, form: dict) -> None:
    handler.jobs.stop()
    handler.redirect(form.get("back") if form.get("back") in ("/generate", "/training") else "/training")


ROUTES = {
    "/": home,
    "/characters": characters,
    "/character": character,
    "/flagged": flagged_images,
    "/image": image,
    "/style.css": style,
    "/downloads": downloads,
    "/exports": export_list,
    "/tryouts": tryout_list,
    "/generate": generate_page,
    "/training": training_page,
    "/jobs/current": current_job,
}
FILE_ROUTES = {"/thumbs/": thumbs, "/exports/": export_file, "/tryouts/": tryout_file, "/generated/": generated_file}
POST_ROUTES = {
    "/generate": start_job(studio.generate_job, generate_page, "/generate"),
    "/training/start": start_job(studio.train_job, training_page, "/training"),
    "/training/resume": start_job(studio.resume_job, training_page, "/training"),
    "/training/tryout": start_job(studio.tryout_job, training_page, "/training"),
    "/jobs/stop": stop_job,
}


def file_route(path: str):
    return next((route for prefix, route in FILE_ROUTES.items() if path.startswith(prefix)), None)


def warm_up(layout: Layout) -> None:
    # Count the slow summaries now, so the first page someone opens does not wait for them.
    with open_db(layout) as db:
        queries.imports(db)
        queries.splits(db)
        if flagged.analyzed(db):
            flagged.status_counts(db)
            first_flag = next(iter(flagged.flag_counts(db, "")), "")
            if first_flag:
                flagged.flagged_images(db, first_flag, "", 1)


def serve(layout: Layout, port: int, jobs: Jobs | None = None) -> ThreadingHTTPServer:
    if not layout.records.exists():
        raise SystemExit("No records yet. Run `pixel import pac lpc-4view` first.")

    # The pages open the records read-only, so bring the file up to date once here.
    connect(layout.records).close()
    threading.Thread(target=warm_up, args=(layout,), daemon=True).start()

    jobs = jobs or Jobs(layout.data / "jobs", layout.data)

    # Only this computer can open it: the data never leaves the machine.
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(layout, jobs))
    server.jobs = jobs

    return server
