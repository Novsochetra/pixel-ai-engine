from pixel_data.dashboard.studio import Invalid

from pixel_server.create.generate_form import form_value

# The API's names for the fields of the old HTML forms, which train_job, resume_job and tryout_job read.
START = {"name": "name", "task": "task", "export": "export", "model": "model", "size": "size", "steps": "steps"}
RESUME = {"run": "run", "steps": "steps"}
TRYOUT = {"run": "run", "checkpoint": "lora", "model": "model", "characters": "rotate"}


def old_fields(body: dict, fields: dict) -> dict:
    return {field: form_value(name, body[name]) for name, field in fields.items() if name in body}


def name_list(value, what: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(name, str) for name in value):
        raise Invalid(f"{what} must be a list of names.")

    return value


# train_job checks each source and its times; here only the shape is checked.
def repeat_map(value) -> dict:
    if not isinstance(value, dict):
        raise Invalid("repeat must map each source to how many times it is shown.")

    return value


# The old HTML form sent each checked source as its own field, which train_job reads as sources_list.
def start_form(body: dict) -> dict:
    return {
        **old_fields(body, START),
        "sources_list": name_list(body.get("sources", []), "sources"),
        "more_exports": name_list(body.get("moreExports", []), "moreExports"),
        "repeat": repeat_map(body.get("repeat", {})),
    }


def resume_form(body: dict) -> dict:
    return old_fields(body, RESUME)


def tryout_form(body: dict) -> dict:
    return old_fields(body, TRYOUT)
