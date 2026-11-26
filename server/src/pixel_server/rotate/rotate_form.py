from pixel_server.animate.animate_form import text_value, view_list

# The API's names for the fields rotate_job reads, as the old HTML forms named them.
FIELDS = {"source": "source", "lora": "lora", "turningModel": "turn_model", "sprite": "sprite"}


# A field left out keeps the default rotate_job gives it.
def rotate_form(body: dict) -> dict:
    form = {field: text_value(name, body[name]) for name, field in FIELDS.items() if name in body}

    if "views" in body:
        form["views_list"] = view_list(body["views"])

    return form
