from importlib.metadata import version

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    return {"ok": True, "version": version("pixel-server")}
