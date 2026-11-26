from urllib.parse import quote


def image_url(image_id: str) -> str:
    return f"/api/images/{quote(image_id)}.png"


def thumb_url(image_id: str) -> str:
    return f"/api/thumbs/{quote(image_id)}.png"


def file_url(folder: str, path: str) -> str:
    return f"/api/files/{folder}/{quote(path)}"


def picture(image_id: str, label: str) -> dict:
    return {"id": image_id, "label": label, "src": image_url(image_id), "thumb": thumb_url(image_id)}
