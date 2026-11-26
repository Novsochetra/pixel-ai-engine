from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request
from pixel_data.dashboard.studio import Invalid

from pixel_server.made.trash import Busy, restore_made, trash_made

router = APIRouter()


def answer(move: Callable[[], dict]) -> dict:
    try:
        return move()
    except Invalid as error:
        raise HTTPException(400, str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except Busy as error:
        raise HTTPException(409, str(error)) from error


# Create and Rotate list data/generated/, Animate data/animated/: one pair of routes serves all three.
@router.post("/api/{kind}/trash")
def trash(request: Request, kind: str, body: dict) -> dict:
    data = request.app.state.layout.data

    return answer(lambda: trash_made(data, kind, body.get("folder"), request.app.state.jobs.current()))


@router.post("/api/{kind}/restore")
def restore(request: Request, kind: str, body: dict) -> dict:
    data = request.app.state.layout.data

    return answer(lambda: restore_made(data, kind, body.get("folder"), body.get("trashed")))
