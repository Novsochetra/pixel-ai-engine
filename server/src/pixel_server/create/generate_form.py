from pixel_data.dashboard import studio

# The API's names for the fields of the old HTML form, which studio.generate_job reads.
FIELDS = {
    "prompt": "prompt",
    "pose": "pose",
    "facing": "facing",
    "characters": "seeds",
    "sprite": "sprite",
    "drawWith": "create_lora",
    "drawingModel": "front_model",
    "turnWith": "lora",
    "turningModel": "turn_model",
}


def form_value(name: str, value) -> str:
    # bool is an int in Python, but "True" characters is not a number anyone meant.
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)

    if not isinstance(value, str):
        raise studio.Invalid(f"{name} must be text or a whole number.")

    return value


# A field left out keeps the default generate_job gives it.
def studio_form(body: dict) -> dict:
    return {field: form_value(name, body[name]) for name, field in FIELDS.items() if name in body}
