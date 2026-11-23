import os
import sqlite3
import threading
from functools import wraps

# Some dashboard numbers count over millions of images and take seconds. They only change when
# `pixel import` or `pixel analyze` writes the records file, so keep each answer until it does.
ANSWERS: dict = {}
LOCK = threading.Lock()


def file_stamp(db: sqlite3.Connection) -> tuple:
    path = db.execute("PRAGMA database_list").fetchone()[2]
    info = os.stat(path)

    return path, info.st_mtime_ns, info.st_size


def until_changed(function):
    @wraps(function)
    def remembered(db: sqlite3.Connection, *args):
        stamp = file_stamp(db)
        key = (function.__qualname__, stamp[0], repr(args))

        with LOCK:
            found = ANSWERS.get(key)
        if found and found[0] == stamp:
            return found[1]

        answer = function(db, *args)
        with LOCK:
            ANSWERS[key] = (stamp, answer)

        return answer

    return remembered
