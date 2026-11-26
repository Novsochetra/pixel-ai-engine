import sqlite3
from collections.abc import Callable

from pixel_data.dashboard.browse_server import open_db
from pixel_data.sources import Layout


# Before the first `pixel import` there is no records file, and sqlite would make an empty one.
def read_records(layout: Layout, read: Callable[[sqlite3.Connection], dict], empty: dict) -> dict:
    if not layout.records.exists():
        return {**empty, "imported": False}

    with open_db(layout) as db:
        return {**read(db), "imported": True}
