from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from pixel_data.dashboard.library import Filters
from pydantic import BaseModel, Field

from pixel_server.library.characters import EMPTY_LIST, character_detail, character_list
from pixel_server.library.records import read_records

router = APIRouter()


class CharacterQuery(BaseModel):
    page: int = Field(1, ge=1)
    q: str = ""
    source: str = ""
    split: str = ""


@router.get("/api/characters")
def characters(request: Request, query: Annotated[CharacterQuery, Query()]) -> dict:
    filters = Filters(query.source, query.split, query.q.strip(), query.page)

    return read_records(request.app.state.layout, lambda db: character_list(db, filters), EMPTY_LIST)


# Character ids hold slashes (pac/train/0), so the id is the rest of the path.
@router.get("/api/characters/{name:path}")
def character(request: Request, name: str) -> dict:
    found = read_records(request.app.state.layout, lambda db: character_detail(db, name) or {}, {})

    if "id" not in found:
        raise HTTPException(404, f"No character {name}.")

    return found
