from pixel_data.dashboard import animate_page, rotate_job, studio
from pixel_data.dashboard.browse_server import UPLOAD_LIMIT

from pixel_server.create.form_options import choices


def rotate_options() -> dict:
    return {
        "models": choices(studio.MODELS),
        "sprites": [{"value": str(size), "label": f"{size} × {size}"} for size in studio.SPRITES],
        "views": list(rotate_job.TURNED),
        "largestUpload": animate_page.LARGEST_UPLOAD,
        "uploadLimit": UPLOAD_LIMIT,
        "defaults": {
            "sprite": rotate_job.DEFAULT_SPRITE,
            "model": rotate_job.DEFAULT_MODEL,
            "views": list(rotate_job.TURNED),
        },
    }
