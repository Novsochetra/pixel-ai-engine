from fastapi import APIRouter, Request

from pixel_server.library.export_list import export_list
from pixel_server.library.tryout_list import tryout_list

router = APIRouter()


@router.get("/api/exports")
def exports(request: Request) -> dict:
    return export_list(request.app.state.layout.data)


@router.get("/api/tryouts")
def tryouts(request: Request, run: str = "") -> dict:
    return tryout_list(request.app.state.layout.data, run)
