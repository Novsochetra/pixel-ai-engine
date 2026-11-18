import argparse
import json
import os
import webbrowser
from pathlib import Path

from huggingface_hub import HfApi

from pixel_data.dashboard.browse_server import serve
from pixel_data.dashboard.build import build_dashboard
from pixel_data.dashboard.page import human_size
from pixel_data.gather.download import gather_source, remote_size
from pixel_data.gather.importer import import_source
from pixel_data.sources import Layout, Source, is_gathered, load_sources, pick_sources


def list_command(sources: list[Source], layout: Layout, sizes: bool) -> None:
    api = HfApi() if sizes else None

    print(f"{'id':<16} {'kind':<12} {'use':<13} {'status':<16} size")
    for source in sources:
        status = "downloaded" if is_gathered(source, layout) else "-"
        size = remote_size(api, source) if api else None
        shown = human_size(size) if size is not None else ""

        print(f"{source.id:<16} {source.kind:<12} {source.use:<13} {status:<16} {shown}")


def chosen_sources(sources: list[Source], args) -> list[Source]:
    if args.ids:
        return pick_sources(sources, args.ids)

    if not args.all:
        raise SystemExit("Name the sources to download (see `pixel list`), or pass --all.")

    return [source for source in sources if args.experimental or not source.is_experimental]


def gather_command(sources: list[Source], layout: Layout, args) -> None:
    for source in chosen_sources(sources, args):
        gather_source(source, layout)

    print("\nDone. Run `pixel dashboard` to look at what you have.")


def import_command(sources: list[Source], layout: Layout, ids: list[str]) -> None:
    for source in pick_sources(sources, ids):
        print(f"== {source.id}")
        entry = import_source(source, layout)
        print(f"  {entry['images']:,} images of {entry['characters']:,} characters")

        for reason, count in json.loads(entry["skipped"]).items():
            print(f"  skipped {count:,}: {reason}")

    print(f"\nRecords are in {layout.records}. Run `pixel browse` to look at them.")


def dashboard_command(sources: list[Source], layout: Layout) -> None:
    page = build_dashboard(sources, layout)

    print(f"\nOpen it: open {page}")


def browse_command(layout: Layout, port: int, open_page: bool) -> None:
    server = serve(layout, port)
    url = f"http://127.0.0.1:{port}/"

    print(f"Browsing {layout.records} at {url} (Ctrl+C to stop)")
    if open_page:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pixel", description="Gather and look at the pixel engine datasets.")
    root.add_argument("--data", type=Path, default=Path(os.environ.get("PIXEL_DATA", "data")), help="where data lives (or set PIXEL_DATA)")
    root.add_argument("--sources", type=Path, default=Path("sources.json"), help="the list of sources")
    commands = root.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("list", help="show every source and whether it is downloaded")
    listing.add_argument("--sizes", action="store_true", help="also ask Hugging Face for download sizes")

    gather = commands.add_parser("gather", help="download sources into data/raw")
    gather.add_argument("ids", nargs="*", help="source ids from `pixel list`")
    gather.add_argument("--all", action="store_true", help="every source except experimental ones")
    gather.add_argument("--experimental", action="store_true", help="with --all, include experimental sources too")

    importing = commands.add_parser("import", help="turn downloaded sources into records, one per image")
    importing.add_argument("ids", nargs="+", help="source ids from `pixel list`")

    commands.add_parser("dashboard", help="build data/reports/dashboard.html")

    browse = commands.add_parser("browse", help="open the records in your web browser")
    browse.add_argument("--port", type=int, default=8777)
    browse.add_argument("--no-open", action="store_true", help="do not open the web browser")

    return root


def main() -> None:
    args = parser().parse_args()
    sources = load_sources(args.sources)
    layout = Layout(args.data.expanduser())

    if args.command == "list":
        list_command(sources, layout, args.sizes)
    elif args.command == "gather":
        gather_command(sources, layout, args)
    elif args.command == "import":
        import_command(sources, layout, args.ids)
    elif args.command == "browse":
        browse_command(layout, args.port, not args.no_open)
    else:
        dashboard_command(sources, layout)
