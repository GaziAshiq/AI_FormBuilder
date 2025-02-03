from typing import Dict, Any, List
import json
from ai_server import fetch_chat_response, process_streaming_response, OLLAMA_MODEL, USE_OLLAMA, OPENAI_MODEL
import uuid
from datetime import datetime, timezone

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
    """Generate validation rules based on field type."""
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
    if USE_OLLAMA:
        return {
            "model": OLLAMA_MODEL,
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
    else:
        return {
            "model": OPENAI_MODEL,
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

IMPORTANT: Return ONLY a JSON object with fields array like this:
{{
    "fields": [
        {{
            "type": "text",
            "label": "Field Label",
            "name": "field_name",
            "required": true,
            "options": [
                {{
                    "value": "1",
                    "label": "Option 1"
                }},
                {{
                    "value": "2",
                    "label": "Option 2"
                }}
            ]
        }}
    ]
}}

Available field types: text, number, radio, dropdown, date, file, image, document
Note: options array only needed for radio and dropdown types."""


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
    try:
        # Extract JSON from response
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = ai_response[json_start:json_end]
            form_data = json.loads(json_str)
            return generate_form_structure(form_data)
    except Exception as e:
        print(f"Error processing response: {e}")
        return {}


def main():
    while True:
        try:
            user_input = input("\nDescribe your survey form (or 'quit' to exit): ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nExiting form generator...")
                break
            
            response = fetch_chat_response(create_prompt(user_input))
            ai_response = process_streaming_response(response)
            
            print("\nGenerating form structure...")
            form_structure = process_ai_response(ai_response)
            
            if form_structure:
                print("\nGenerated Form Structure:")
                print(json.dumps(form_structure, indent=2))
            else:
                print("\nFailed to generate form structure")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled. Type 'quit' to exit properly.")
            continue
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            continue


if __name__ == "__main__":
    main()
