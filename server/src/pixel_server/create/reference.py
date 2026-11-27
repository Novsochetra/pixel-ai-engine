from pathlib import Path

from pixel_data.dashboard import animate
from pixel_data.dashboard.studio import Invalid


# Only a picture the dashboard saved itself, so the browser can never point the job at another file.
def reference_args(data: Path, value) -> list[str]:
    if value is None or value == "":
        return []

    if not isinstance(value, str) or value not in {f"uploads/{name}" for name in animate.uploads(data)}:
        raise Invalid("Pick a reference picture from your uploads.")

    return ["--reference", str(data.resolve() / value)]
