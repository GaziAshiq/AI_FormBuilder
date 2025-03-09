FIELD_TYPES = ["text", "number", "radio", "dropdown", "date", "file", "section"]

def validate_form_structure(form_data: dict) -> tuple[bool, str]:
    if "fields" not in form_data["form_data"]:
        return False, "Missing 'fields' in form_data"

    field_names = set()
    for field in form_data["form_data"]["fields"]:
        if not all(key in field for key in ["name", "label", "type", "required"]):
            return False, f"Field missing required keys: {field}"

        if field["type"] not in FIELD_TYPES:
            return False, f"Invalid field type: {field['type']}"

        if field["type"] in ["radio", "dropdown"] and "options" not in field:
            return False, f"Field '{field['name']}' requires 'options'"

        if field["name"] in field_names:
            return False, f"Duplicate field name: {field['name']}"
        field_names.add(field["name"])

        if field["type"] == "section" and "fields" not in field:
            return False, f"Section '{field['name']}' requires nested 'fields'"

    return True, "Valid form structure"