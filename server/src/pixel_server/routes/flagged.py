from typing import Annotated

from fastapi import APIRouter, Query, Request

from pixel_server.library.flagged_list import EMPTY_FLAGGED, flagged_list
from pixel_server.library.records import read_records

router = APIRouter()


@router.get("/api/flagged")
def flagged(request: Request, flag: str = "", page: Annotated[int, Query(ge=1)] = 1) -> dict:
    return read_records(request.app.state.layout, lambda db: flagged_list(db, flag, page), EMPTY_FLAGGED)
