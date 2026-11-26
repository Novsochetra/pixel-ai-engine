import argparse
import os
from pathlib import Path

import uvicorn
from pixel_data.dashboard.jobs import Jobs

from pixel_server.app import create_app

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA = ROOT / "dataset" / "data"
UI_DIST = ROOT / "ui" / "dist"


def build_app():
    data = Path(os.environ.get("PIXEL_DATA", DEFAULT_DATA))

    return create_app(Jobs(data / "jobs", data), UI_DIST)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the pixel engine dashboard API")
    parser.add_argument("--port", type=int, default=8780)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="the dataset/data folder")
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
