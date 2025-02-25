import json


def validate_form_structure(form_data: dict) -> bool:
    required_keys = ["message", "form_data"]
    if not all(key in form_data for key in required_keys):
        return False

    if "fields" not in form_data["form_data"]:
        return False

    for filed in form_data["form_data"]["fields"]:
        if not all(key in filed for key in ["name", "label", "type", "required"]):
            return False

    return True
