from typing import Dict, Any, List
import json
from ai_server import fetch_chat_response, process_streaming_response, OLLAMA_MODEL, USE_OLLAMA, OPENAI_MODEL
import uuid

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
    return f"""Generate a SINGLE form for: {user_input}

IMPORTANT: Return ONLY valid JSON for ONE form.

Required structure:
{{
    "fields": [
        {{
            "name": "field_name",
            "type": "field_type",
            "label": "Field Label",
            "required": true,
            "options": [
                {{"value": "1", "label": "Option 1"}},  // Note: use "label", not "display"
                {{"value": "2", "label": "Option 2"}}
            ]
        }}
    ]
}}

Available types: text, number, email, date, file, image, dropdown, radio, checkbox
Note: options array is only needed for dropdown, radio, and checkbox types.
For gender options, use: {{"value": "male", "label": "Male"}} format."""

def generate_form_field(field_data: Dict[str, Any], form_id: str) -> Dict[str, Any]:
    field_name = field_data["name"].lower()
    field_type = field_data["type"]
    
    return {
        "Name": field_name,
        "DataElementTypeId": FIELD_TYPE_MAPPING.get(field_type, "1"),
        "TextId": None,
        "InputType": None,
        "IsRequired": field_data.get("required", False),
        "DefaultValue": None,
        "DisplayText": field_data["label"],
        "DataElementColumnName": field_name.replace(" ", "_"),
        "IsFixed": False,
        "DataElementBase": None,
        "DataElementType": None,
        "DataElementOptions": [
            {
                "Name": opt["label"],
                "TextId": None,
                "Value": opt["value"],
                "SortOrder": idx + 1,
                "DataElementId": f"{form_id}:{field_name}",
                "DataElementBaseOptionId": None,
                "CreatedBy": "system",
                "CreateTime": None,
                "LastModifiedBy": None,
                "LastModifiedTime": None,
                "IsDeleted": False,
                "Id": generate_uuid()
            }
            for idx, opt in enumerate(field_data.get("options", []))
        ] if field_data.get("options") else None,
        "SurveyFormId": None,
        "Serial": 0,
        "IsPublished": None,
        "RepeaterTableName": None,
        "IsDeleted": False,
        "Id": f"{form_id}:{field_name}",
        "ValidationRules": create_validation_rules(field_type, field_name)
    }

def process_ai_response(ai_response: str) -> Dict[str, Any]:
    try:
        # Find the complete JSON object
        json_start = ai_response.find('{\n    "fields"')
        json_end = ai_response.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_str = ai_response[json_start:json_end]
            # Parse the JSON portion
            form_data = json.loads(json_str)
            
            # Generate form ID
            form_id = generate_uuid()
            
            # Generate form fields
            fields = [generate_form_field(field, form_id) for field in form_data["fields"]]
            
            return {
                "DataElements": fields,
                "DraftSurveyDataElementMembers": [
                    {
                        "DraftSurveyFormId": form_id,
                        "DataElementId": f"{form_id}:{field['Name']}",
                        "IsGroup": False,
                        "IsFixed": False,
                        "SortOrder": idx + 1,
                        "RepeaterTableName": None,
                        "CreatedBy": "system",
                        "CreateTime": None,
                        "LastModifiedBy": None,
                        "LastModifiedTime": None,
                        "IsDeleted": None,
                        "Id": generate_uuid()
                    } for idx, field in enumerate(fields)
                ],
                "DataElementOptions": [
                    option
                    for field in fields
                    if field["DataElementOptions"]
                    for option in field["DataElementOptions"]
                ],
                "FormId": form_id
            }
        else:
            print("No valid JSON found in response")
            return {}
            
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print("Invalid JSON content:", json_str if 'json_str' in locals() else "No JSON found")
        return {}
    except Exception as e:
        print(f"Error processing response: {e}")
        print("Response content:", ai_response)
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
                
            # 1. Generate AI prompt
            prompt = create_prompt(user_input)
            
            # 2. Get AI response
            response = fetch_chat_response(prompt)
            if response is None:
                print("Failed to get response from AI service")
                continue
                
            ai_response = process_streaming_response(response)
            if not ai_response:
                print("Empty response from AI service")
                continue
            
            # 3. Process response into form structure
            print("\nExtracting JSON from response...")
            form_structure = process_ai_response(ai_response)
            
            # 4. Output the result
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
