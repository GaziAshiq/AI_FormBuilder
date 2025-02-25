import json
import os
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()


def _create_messages(context: Dict) -> list:
    system_prompt = """You are a form generation assistant. Follow these rules:
    1. ONLY create fields that are explicitly requested by the user
    2. When user questions about a field, remove it if they didn't request it, otherwise keep it
    3. Keep track of user's original request and only maintain those fields
    4. If user asks "did I tell you to add X?", check if X is in the original request, if not, remove it
    5. Acknowledge mistakes in the message field

    IMPORTANT: ALWAYS respond with ONLY valid JSON in this EXACT format, no other text:
    {
    "message": "Form updated: Added name, email, and address fields as requested",
    "form_data": {
        "fields": [
            {
                "name": "name",
                "label": "Name",
                "type": "text",
                "required": true
            },
            {
                "name": "email",
                "label": "Email",
                "type": "email",
                "required": true
            },
            {
                "name": "address",
                "label": "Address",
                "type": "text",
                "required": true
            },
            {
                "name": "picture",
                "label": "Upload Picture",
                "type": "file",
                "required": true
            }
        ]
    }
    }

    Available field types: text, number, radio, dropdown, date, file
    For radio/dropdown, include "options" array with "value" and "label"
    Use snake_case for field names
    Keep all existing fields when adding new ones"""

    # Create a context message based on current form state
    if context.get("current_form") and context["current_form"].get("fields"):
        user_message = f"""Current form has these fields:
        {json.dumps(context['current_form'], indent=2)}

        User request: {context['request']}

        Remember to:
        1. Keep all existing fields
        2. Add/modify fields based on the request
        3. Return complete form with all fields"""
    else:
        user_message = context['request']

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

def process_streaming_response(response) -> str:
    """Process streaming response, capturing only valid JSON"""
    print("\nDebug: Processing AI response...")
    buffer = ""
    in_json = False
    json_depth = 0
    
    try:
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content
                if content:
                    # Skip everything until we find the first '{'
                    if '{' in content and not in_json:
                        in_json = True
                        start_pos = content.find('{')
                        content = content[start_pos:]
                        
                    if in_json:
                        # Count JSON nesting
                        json_depth += content.count('{') - content.count('}')
                        buffer += content
                        
                        # Print only JSON content
                        print(content, end='', flush=True)
                        
                        # If we've closed all JSON brackets, we're done
                        if json_depth == 0:
                            break
        
        # Validate and clean JSON
        try:
            # Parse JSON to validate it
            json_obj = json.loads(buffer)
            # Convert back to string with proper formatting
            return json.dumps(json_obj)
        except json.JSONDecodeError:
            print("\nDebug: Invalid JSON structure")
            return ""
            
    except Exception as e:
        print(f"\nError in process_streaming_response: {str(e)}")
        return ""


class AIClient:
    def __init__(self, use_ollama: bool = True):
        self.use_ollama = use_ollama
        self.current_form = {"fields": []}

        if use_ollama:
            self.client = OpenAI(
                base_url='http://192.168.0.225:11434/v1',
                api_key='ollama',
            )
            # self.model = "deepseek-r1:14b"
            self.model = "deepseek-r1:8b"
            # self.model = "deepseek-r1:7b"
        else:
            self.client = OpenAI(
                api_key=os.getenv("API_KEY"),
                base_url="https://api.deepseek.com/beta",
            )
            self.model = "deepseek-chat"

    def fetch_chat_response(self, content: str, current_form: Dict = None) -> str:
        """Send request to the appropriate API endpoint with context"""
        try:
            print("\nDebug: Creating context...")
            context = {
                "current_form": current_form if current_form else {"fields": []},
                "request": content
            }

            print("\nDebug: Generating messages...")
            messages = _create_messages(context)

            print(f"\nDebug: Connecting to {self.client.base_url}")
            print(f"Debug: Using model {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )

            return process_streaming_response(response)

        except Exception as e:
            print(f"Error in fetch_chat_response: {str(e)}")
            return ""


def main():
    # Create AI client (True for Ollama, False for OpenAI)
    client = AIClient(use_ollama=True)

    while True:
        user_input = input("\nDescribe your form (or 'quit' to exit): ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        response = client.fetch_chat_response(user_input)


if __name__ == "__main__":
    main()
