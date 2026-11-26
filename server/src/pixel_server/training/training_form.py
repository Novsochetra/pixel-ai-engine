from pixel_data.dashboard.studio import Invalid

from pixel_server.create.generate_form import form_value

# The API's names for the fields of the old HTML forms, which train_job, resume_job and tryout_job read.
START = {"name": "name", "task": "task", "export": "export", "model": "model", "size": "size", "steps": "steps"}
RESUME = {"run": "run", "steps": "steps"}
TRYOUT = {"run": "run", "checkpoint": "lora", "model": "model", "characters": "rotate"}


def old_fields(body: dict, fields: dict) -> dict:
    return {field: form_value(name, body[name]) for name, field in fields.items() if name in body}


def source_list(value) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(source, str) for source in value):
        raise Invalid("sources must be a list of source names.")

    return value


# The old HTML form sent each checked source as its own field, which train_job reads as sources_list.
def start_form(body: dict) -> dict:
    return {**old_fields(body, START), "sources_list": source_list(body.get("sources", []))}


def resume_form(body: dict) -> dict:
    return old_fields(body, RESUME)


def tryout_form(body: dict) -> dict:
    return old_fields(body, TRYOUT)
