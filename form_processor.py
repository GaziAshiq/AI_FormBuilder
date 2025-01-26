import spacy
import json

# Load the spaCy Transformer-based model
nlp = spacy.load("en_core_web_trf")

# Initialize an empty form JSON structure
form_data = {"fields": []}


def process_input(input_text, form_data_p):
    """
    Process user input to update the form data.

    Args:
        input_text (str): The user input describing the form field.
        form_data_p (dict): The current form data structure.

    Returns:
        dict: The updated form data structure.
    """
    # Use spaCy to parse the input text
    doc = nlp(input_text)
    field = {}

    if "add a" in input_text.lower():
        # Determine the type of field
        field_type = "text"
        if "email" in input_text.lower():
            field_type = "email"
        elif "radio" in input_text.lower() or "multiple choice" in input_text.lower():
            field_type = "radio"
        elif "checkbox" in input_text.lower():
            field_type = "checkbox"
        elif "textarea" in input_text.lower():
            field_type = "textarea"
        elif "date" in input_text.lower():
            field_type = "date"
        elif "person" in input_text.lower():
            field_type = "person"
        elif "files" in input_text.lower() or "media" in input_text.lower():
            field_type = "files"
        elif "number" in input_text.lower():
            field_type = "number"
        elif "url" in input_text.lower():
            field_type = "url"
        elif "phone" in input_text.lower():
            field_type = "phone"

        # Extract the label
        label = None
        for chunk in doc.noun_chunks:
            if any(word in chunk.text.lower() for word in ["for", "question", "field"]):
                label = chunk.text
                break

        # Fallback for label if no entity detected
        if not label:
            label = " ".join([token.text for token in doc if token.pos_ in ["NOUN", "PROPN"]]).strip()

        # Add options if it's a choice field
        options = []
        if field_type in ["radio", "checkbox"] and "with options" in input_text.lower():
            options_text = input_text.lower().split("with options")[1].strip()
            options = [opt.strip() for opt in options_text.split(",") if opt.strip()]

        # Populate the field object
        field = {
            "type": field_type,
            "label": label,
            "name": label.lower().replace(" ", "_").strip(),
            "required": "required" in input_text.lower(),
        }

        if options:
            field["options"] = [{"value": opt.lower(), "label": opt} for opt in options]

        # Append the new field to the form_data
        if field_type and label:
            form_data_p["fields"].append(field)

    elif "make" in input_text.lower() and "optional" in input_text.lower():
        # Detect the field to update
        for field in form_data_p["fields"]:
            if any(word in input_text.lower() for word in field["label"].lower().split()):
                field["required"] = False

    return form_data_p


# region [Example]
# Example inputs
user_inputs = [
    "Add a text field for name",
    "Add a multiple choice question for gender with options Male, Female, Other",
    "Make the gender question optional",
    "Add a checkbox field for interests",
    "Add a email field for email",
    "Add a date field for date of birth",
    "Add a person field for assignee",
    "Add a files field for profile picture upload",
    "Add a number field for age",
    "Add a URL field for website",
    "Add a phone field for contact number",
]

# Process each input and update the form_data
for user_input in user_inputs:
    form_data = process_input(user_input, form_data)

# Print the resulting JSON structure
print(json.dumps(form_data, indent=2))
# endregion
