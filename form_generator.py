from typing import Dict, Any
import json
import uuid
from datetime import datetime, timezone
from ai_server import AIClient

FIELD_TYPE_MAPPING = {
    "text": "1",
    "number": "2",
    "email": "3",
    "date": "4",
    "file": "5",
    "image": "13",
    "dropdown": "8",
    "radio": "8",
    "checkbox": "9"
}


def generate_uuid() -> str:
    return str(uuid.uuid4()).replace('-', '')


def create_validation_rules(field_type: str, field_name: str) -> Dict[str, Any]:
    """Generate validation rules based on a field type."""
    if field_type == "number" and field_name.lower() == "age":
        return {
            "queryWithNames": "{age} >= 0 and {age} <= 150",
            "queryWithIds": "{age} >= 0 and {age} <= 150"
        }
    return {
        "queryWithIds": "",
        "queryWithNames": ""
    }


def create_chat_message(content: str) -> Dict[str, Any]:
    """Create a properly formatted chat message."""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are a form generation assistant. You MUST respond with ONLY valid JSON, no explanations or additional text."
            },
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": True
    }


def create_prompt(user_input: str) -> str:
    return f"""Generate a form for: {user_input}

Please create a form with appropriate fields. Each field should have:
- type (text, number, radio, dropdown, date, file, image)
- label (user-friendly display name)
- name (snake_case identifier)
- required (boolean)
- options (array, only for radio/dropdown)"""


def generate_form_structure(form_data: Dict[str, Any]) -> Dict[str, Any]:
    form_id = generate_uuid()
    current_time = datetime.now(timezone.utc).isoformat()

    data_elements = []
    draft_members = []
    data_element_options = []

    for idx, field in enumerate(form_data["fields"], 1):
        field_id = f"{form_id}:{field['name']}"

        # Map field types to DataElementTypeId
        type_mapping = {
            "text": "1",
            "number": "2",
            "email": "3",
            "date": "4",
            "file": "5",
            "image": "13",
            "radio": "8",
            "dropdown": "8"
        }

        # Create DataElement
        data_element = {
            "Name": field["name"],
            "DataElementBaseId": None,
            "DataElementTypeId": type_mapping.get(field["type"], "1"),
            "TextId": None,
            "InputType": None,
            "IsRequired": field.get("required", False),
            "DefaultValue": None,
            "DisplayText": field["label"],
            "DataElementColumnName": field["name"],
            "IsFixed": False,
            "DataElementBase": None,
            "DataElementType": None,
            "DataElementOptions": None,
            "SurveyFormId": None,
            "Serial": 0,
            "IsPublished": None,
            "RepeaterTableName": None,
            "CreatedBy": "system",
            "CreateTime": current_time,
            "LastModifiedBy": None,
            "LastModifiedTime": None,
            "IsDeleted": False,
            "Id": field_id
        }

        # Handle options for radio/dropdown
        if field.get("options"):
            options = []
            for opt_idx, opt in enumerate(field["options"], 1):
                option_id = generate_uuid()
                option = {
                    "Name": opt["label"],
                    "TextId": None,
                    "Value": str(opt["value"]),
                    "SortOrder": opt_idx,
                    "DataElementId": field_id,
                    "DataElementBaseOptionId": None,
                    "CreatedBy": "system",
                    "CreateTime": current_time,
                    "LastModifiedBy": None,
                    "LastModifiedTime": None,
                    "IsDeleted": False,
                    "Id": option_id
                }
                options.append(option)
                data_element_options.append(option)
            data_element["DataElementOptions"] = options

        data_elements.append(data_element)

        # Create DraftSurveyDataElementMember
        draft_member = {
            "DraftSurveyFormId": form_id,
            "DataElementId": field_id,
            "IsGroup": False,
            "IsFixed": False,
            "SortOrder": idx,
            "RepeaterTableName": None,
            "CreatedBy": "system",
            "CreateTime": current_time,
            "LastModifiedBy": None,
            "LastModifiedTime": None,
            "IsDeleted": None,
            "Id": generate_uuid()
        }
        draft_members.append(draft_member)

    return {
        "DataElements": data_elements,
        "DraftSurveyDataElementMembers": draft_members,
        "DataElementOptions": data_element_options
    }


def process_ai_response(ai_response: str) -> Dict[str, Any]:
    """Process the AI response and extract the form data"""
    try:
        print("\nDebug: Processing AI response...")

        if not ai_response:
            print("Debug: Empty AI response")
            return {}

        # Parse the JSON
        form_data = json.loads(ai_response)

        # Validate response structure
        if not isinstance(form_data, dict):
            print("Debug: Response is not a dictionary")
            return {}

        if "form_data" not in form_data:
            print("Debug: Missing form_data key")
            return {}

        if "fields" not in form_data["form_data"]:
            print("Debug: Missing fields array")
            return {}

        # Debug: Show field summary
        print("\nForm field summary:")
        for field in form_data["form_data"]["fields"]:
            print(f"- {field['name']} ({field['type']})")

        return form_data["form_data"]

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print("Invalid JSON content:", ai_response)
        return {}
    except Exception as e:
        print(f"Error processing response: {e}")
        return {}


def main():
    client = AIClient(use_ollama=True)
    current_form = {"fields": []}

    print("\nForm Generator")
    print("Commands:")
    print("- Type your form requirements")
    print("- 'show' to see current form")
    print("- 'quit' to exit")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nWhat would you like to do? ").strip()
            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nExiting form generator...")
                break

            if user_input.lower() == 'show':
                if current_form["fields"]:
                    print("\nCurrent form structure:")
                    print(json.dumps(current_form, indent=2))
                else:
                    print("\nNo form created yet")
                continue  # Skip AI processing for 'show' command

            # Get AI response
            print("\nGenerating form structure...")
            ai_response = client.fetch_chat_response(user_input, current_form)

            # Process response
            form_data = process_ai_response(ai_response)

            # Update current form
            if form_data and "fields" in form_data:
                current_form = form_data
                print("\nUpdated form structure:")
                print(json.dumps(current_form, indent=2))
            else:
                print("\nFailed to update form structure")

        except KeyboardInterrupt:
            print("\nOperation cancelled. Type 'quit' to exit properly.")
            continue
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            continue


if __name__ == "__main__":
    main()
