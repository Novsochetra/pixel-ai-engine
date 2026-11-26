from pixel_data.dashboard.studio import Invalid

TEXT_FIELDS = ("source", "subject", "actions", "size", "frames")


def text_value(name: str, value) -> str:
    if not isinstance(value, str):
        raise Invalid(f"{name} must be text.")

    return value


def view_list(value) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(view, str) for view in value):
        raise Invalid("views must be a list of view names.")

    return value


# The old HTML form sent each checked view as its own field, which animate_job reads as views_list.
def old_form(body: dict) -> dict:
    form = {name: text_value(name, body[name]) for name in TEXT_FIELDS if name in body}

    if "views" in body:
        form["views_list"] = view_list(body["views"])

    return form
