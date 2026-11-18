import json
import subprocess
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from pixel_data.sources import DROP_NOTE, SOURCE_RECORD, Layout, Source, folder_size


def write_record(source: Source, folder: Path) -> None:
    file_count, byte_count = folder_size(folder)
    record = {
        "id": source.id,
        "repo": source.repo,
        "revision": source.revision,
        "gathered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": file_count,
        "bytes": byte_count,
    }

    (folder / SOURCE_RECORD).write_text(json.dumps(record, indent=2))


def gather_huggingface(source: Source, folder: Path) -> None:
    snapshot_download(
        repo_id=source.repo,
        repo_type="dataset",
        revision=source.revision,
        local_dir=folder,
        allow_patterns=source.allow or None,
    )


def run_git(folder: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(folder), *args], check=True)


def gather_git(source: Source, folder: Path) -> None:
    if not (folder / ".git").exists():
        run_git(folder, "init", "--quiet")
        run_git(folder, "remote", "add", "origin", source.repo)

    run_git(folder, "fetch", "--depth", "1", "origin", source.revision)
    run_git(folder, "checkout", "--quiet", "FETCH_HEAD")


def prepare_manual(source: Source, folder: Path) -> None:
    links = "\n".join(f"- {link}" for link in source.links)
    note = f"Download these by hand and put the files (zips are fine) in this folder:\n\n{links}\n"

    (folder / DROP_NOTE).write_text(note)
    print(f"  manual: download by hand into {folder}")
    print(links)


def gather_source(source: Source, layout: Layout) -> None:
    folder = layout.source_dir(source)
    folder.mkdir(parents=True, exist_ok=True)

    print(f"\n== {source.id} ({source.kind}) -> {folder}")
    if source.kind == "manual":
        prepare_manual(source, folder)
        return

    if source.kind == "git":
        gather_git(source, folder)
    else:
        gather_huggingface(source, folder)

    write_record(source, folder)


def remote_size(api: HfApi, source: Source) -> int | None:
    if source.kind != "huggingface":
        return None

    entries = api.list_repo_tree(
        source.repo, repo_type="dataset", revision=source.revision, recursive=True
    )
    sizes = [
        entry.size
        for entry in entries
        if hasattr(entry, "size") and matches(entry.path, source.allow)
    ]

    return sum(sizes)


def matches(path: str, patterns: list[str]) -> bool:
    if not patterns:
        return True

    return any(fnmatch(path, pattern) for pattern in patterns)
