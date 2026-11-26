import argparse
import os
import threading
from pathlib import Path

import uvicorn
from pixel_data.dashboard.browse_server import warm_up
from pixel_data.dashboard.jobs import Jobs
from pixel_data.records import connect
from pixel_data.sources import Layout

from pixel_server.app import create_app

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA = ROOT / "dataset" / "data"
UI_DIST = ROOT / "ui" / "dist"


def prepare_records(layout: Layout) -> None:
    if not layout.records.exists():
        return

    # The routes open the records read-only, so bring the file up to date once here.
    connect(layout.records).close()

    # Counting flags over millions of images takes seconds; do it now, not on the first page.
    threading.Thread(target=warm_up, args=(layout,), daemon=True).start()


def build_app():
    data = Path(os.environ.get("PIXEL_DATA", DEFAULT_DATA))
    prepare_records(Layout(data))

    return create_app(Jobs(data / "jobs", data), UI_DIST)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the pixel engine dashboard API")
    parser.add_argument("--port", type=int, default=8780)
    data = os.environ.get("PIXEL_DATA", DEFAULT_DATA)
    parser.add_argument("--data", type=Path, default=data, help="the dataset/data folder (or PIXEL_DATA)")
    parser.add_argument("--reload", action="store_true", help="restart when a server file changes")
    args = parser.parse_args()

    # uvicorn builds the app again in each reloaded process, so the folder goes through the environment.
    os.environ["PIXEL_DATA"] = str(args.data.resolve())

    # Only this computer can open it: the data never leaves the machine.
    uvicorn.run(
        "pixel_server.main:build_app",
        factory=True,
        host="127.0.0.1",
        port=args.port,
        reload=args.reload,
        reload_dirs=[str(Path(__file__).parent)] if args.reload else None,
    )
