from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()


class AIClient:
    def __init__(self, use_ollama: bool = True):
        self.use_ollama = use_ollama
        self.current_form = {"fields": []}

        if use_ollama:
            self.client = OpenAI(
                base_url='http://192.168.0.225:11434/v1',
                api_key='ollama',
            )
            self.model = "deepseek-r1:8b"
        else:
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            self.model = "gpt-3.5-turbo"

    def _create_messages(self, context: Dict) -> list:
        system_prompt = """You are a form generation assistant. 
IMPORTANT: ALWAYS respond with ONLY valid JSON in this EXACT format, no other text:
{
    "message": "Form updated successfully!",
    "form_data": {
        "fields": [
            {
                "type": "text",
                "label": "Field Label",
                "name": "field_name",
                "required": false
            }
        ]
    }
}

Available field types: text, number, radio, dropdown, date, file
For radio/dropdown, include "options" array with "value" and "label"
Use snake_case for field names
Keep all existing fields when adding new ones"""

        # Create context message based on current form state
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

    def fetch_chat_response(self, content: str, current_form: Dict = None) -> str:
        """Send request to appropriate API endpoint with context"""
        try:
            print("\nDebug: Creating context...")
            context = {
                "current_form": current_form if current_form else {"fields": []},
                "request": content
            }

            print("\nDebug: Generating messages...")
            messages = self._create_messages(context)

            print(f"\nDebug: Connecting to {self.client.base_url}")
            print(f"Debug: Using model {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )

            return self.process_streaming_response(response)

        except Exception as e:
            print(f"Error in fetch_chat_response: {str(e)}")
            return ""

    def process_streaming_response(self, response) -> str:
        """Process streaming response, capturing only valid JSON"""
        print("\nDebug: Processing AI response...")
        json_content = ""
        buffer = ""
        json_started = False

        try:
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        # Start capturing when we see the first '{'
                        if '{' in content and not json_started:
                            json_started = True
                            buffer = content[content.find('{'):]
                        # Keep capturing if we've started
                        elif json_started:
                            buffer += content

                        # Print for debugging
                        print(content, end='', flush=True)

            # Clean up the buffer to get only the JSON part
            if buffer:
                json_start = buffer.find('{')
                json_end = buffer.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_content = buffer[json_start:json_end]

                    # Validate JSON
                    try:
                        json.loads(json_content)
                        return json_content
                    except json.JSONDecodeError:
                        print("\nDebug: Invalid JSON structure")
                        return ""

            return ""

        except Exception as e:
            print(f"\nError in process_streaming_response: {str(e)}")
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
