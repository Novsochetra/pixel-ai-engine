import json
from dataclasses import dataclass, field
from pathlib import Path

SOURCE_RECORD = "_source.json"
DROP_NOTE = "DROP-FILES-HERE.txt"


@dataclass
class Source:
    id: str
    kind: str
    license: str
    use: str
    tasks: list[str]
    notes: str = ""
    repo: str = ""
    revision: str = ""
    allow: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    @property
    def is_experimental(self) -> bool:
        return self.use == "experimental"


@dataclass
class Layout:
    data: Path

    @property
    def raw(self) -> Path:
        return self.data / "raw"

    @property
    def reports(self) -> Path:
        return self.data / "reports"

    @property
    def records(self) -> Path:
        return self.data / "records.sqlite"

    def source_dir(self, source: Source) -> Path:
        if source.is_experimental:
            return self.raw / "_experimental" / source.id

        return self.raw / source.id


def load_sources(path: Path) -> list[Source]:
    entries = json.loads(path.read_text())["sources"]

    return [Source(**entry) for entry in entries]


def pick_sources(sources: list[Source], ids: list[str]) -> list[Source]:
    known = {source.id: source for source in sources}
    unknown = [source_id for source_id in ids if source_id not in known]

    if unknown:
        raise SystemExit(f"Unknown source: {', '.join(unknown)}. Run `pixel list` to see them.")

    return [known[source_id] for source_id in ids]


def read_record(folder: Path) -> dict | None:
    record = folder / SOURCE_RECORD

    if not record.exists():
        return None

    return json.loads(record.read_text())


def has_manual_files(folder: Path) -> bool:
    if not folder.exists():
        return False

    return any(path.name != DROP_NOTE for path in folder.iterdir())


def is_gathered(source: Source, layout: Layout) -> bool:
    folder = layout.source_dir(source)

    if source.kind == "manual":
        return has_manual_files(folder)

    return read_record(folder) is not None


def folder_size(folder: Path) -> tuple[int, int]:
    files = [path for path in folder.rglob("*") if path.is_file() and not {".cache", ".git"} & set(path.parts)]

    return len(files), sum(path.stat().st_size for path in files)
