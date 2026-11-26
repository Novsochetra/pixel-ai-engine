import argparse
import json
import os
import webbrowser
from pathlib import Path

from huggingface_hub import HfApi

from pixel_data.analyze.rules import FLAGS
from pixel_data.analyze.run import analyze
from pixel_data.dashboard.browse_server import serve
from pixel_data.dashboard.build import build_dashboard
from pixel_data.export.run import export
from pixel_data.dashboard.page import human_size
from pixel_data.gather.download import gather_source, remote_size
from pixel_data.gather.importer import import_source
from pixel_data.gather.pixellab import gather_pixellab
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

    return [
        source
        for source in sources
        if not source.costs_money and (args.experimental or not source.is_experimental)
    ]


def gather_command(sources: list[Source], layout: Layout, args) -> None:
    for source in chosen_sources(sources, args):
        if source.costs_money:
            print(f"\n== {source.id} (paid calls) -> {layout.source_dir(source)}")
            folder = args.sources.parent
            gather_pixellab(source, layout, folder / "pixellab" / "plan.json", folder / ".env", args.count, args.parallel, skip=args.skip)
        else:
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


def analyze_command(layout: Layout, ids: list[str]) -> None:
    result = analyze(layout, ids)

    print(f"\n{result['copies']:,} characters are exact copies of another; {result['groups']:,} groups of near-identical characters.")
    for source, counts in result["summary"].items():
        statuses = ", ".join(f"{status} {counts[f'status:{status}']:,}" for status in ("ok", "fix", "check", "drop"))
        print(f"\n== {source}: {statuses}")

        for flag, (meaning, _) in FLAGS.items():
            if counts[flag]:
                print(f"  {flag:<16} {counts[flag]:>8,}  {meaning}")

    print("\nRun `pixel browse` and open Flagged to look at them.")


def export_command(sources: list[Source], layout: Layout, args) -> None:
    summary = export(layout, sources, args.name, args.include_check, args.experimental)

    print(f"\n== {summary['name']}")
    for split, counts in summary["characters"].items():
        parts = ", ".join(f"{source} {count:,}" for source, count in counts.items())
        print(f"  {split:<6} {sum(counts.values()):>7,} characters ({parts})")

    for reason, count in summary["left_out"].items():
        print(f"  left out {count:,}: {reason}")

    leaks = summary["leaks"]
    print(f"  leak checks: {leaks['groups_in_two_splits']} groups and {leaks['pictures_in_two_splits']} pictures in two splits")
    print(f"\nWritten to {layout.data / 'exports' / summary['name']}")


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
    finally:
        # A job started from the page stops with it, so none keeps running unseen.
        if server.jobs.current():
            print("Stopping the running job...")
            server.jobs.stop()


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pixel", description="Gather and look at the pixel engine datasets.")
    root.add_argument("--data", type=Path, default=Path(os.environ.get("PIXEL_DATA", "data")), help="where data lives (or set PIXEL_DATA)")
    root.add_argument("--sources", type=Path, default=Path("sources.json"), help="the list of sources")
    commands = root.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("list", help="show every source and whether it is downloaded")
    listing.add_argument("--sizes", action="store_true", help="also ask Hugging Face for download sizes")

    gather = commands.add_parser("gather", help="download sources into data/raw")
    gather.add_argument("ids", nargs="*", help="source ids from `pixel list`")
    gather.add_argument("--all", action="store_true", help="every free source except experimental ones")
    gather.add_argument("--experimental", action="store_true", help="with --all, include experimental sources too")
    gather.add_argument("--count", type=int, default=5, help="pixellab: how many new characters to make (each is a paid call)")
    gather.add_argument("--parallel", type=int, default=2, help="pixellab: characters made at the same time")
    gather.add_argument("--skip", type=int, default=0, help="pixellab: leave the first N plan entries to another run")

    importing = commands.add_parser("import", help="turn downloaded sources into records, one per image")
    importing.add_argument("ids", nargs="+", help="source ids from `pixel list`")

    analyzing = commands.add_parser("analyze", help="measure every imported image and flag bad ones")
    analyzing.add_argument("ids", nargs="*", help="sources to measure again (default: every imported source)")

    exporting = commands.add_parser("export", help="write the training files: fixed PNGs split by character")
    exporting.add_argument("name", nargs="?", default="rotation-v1", help="folder name under data/exports")
    exporting.add_argument("--include-check", action="store_true", help="also take images marked check")
    exporting.add_argument("--experimental", action="store_true", help="also take experimental sources")

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
    elif args.command == "analyze":
        analyze_command(layout, args.ids)
    elif args.command == "export":
        export_command(sources, layout, args)
    elif args.command == "browse":
        browse_command(layout, args.port, not args.no_open)
    else:
        dashboard_command(sources, layout)
