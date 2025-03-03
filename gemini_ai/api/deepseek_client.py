import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from utils.constants import deepseek_instruction
from dotenv import load_dotenv

load_dotenv()


class DeepSeekClient:
    """Client for interacting with DeepSeek API to generate form data."""

    def __init__(self):
        """Initialize the DeepSeek client with API configuration."""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")

        # Configure OpenAI client to use DeepSeek API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/beta"
        )
        self.model = "deepseek-chat"
        self.system_prompt = deepseek_instruction

    def generate_form(self, prompt_input: str, current_form: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a form based on user input using DeepSeek model.

        Args:
            prompt_input: The user's form requirements.
            current_form: The existing form structure, if any.

        Returns:
            Dictionary containing the generated or updated form data.
        """
        try:
            if current_form is None:
                current_form = {"fields": []}

            context = {
                "current_form": current_form,
                "request": prompt_input
            }

            messages = self._create_messages(context)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )

            response_text = self._process_streaming_response(response)
            return self._parse_response(response_text)

        except Exception as e:
            return {
                "message": f"Error: {str(e)}",
                "form_data": {"fields": []}
            }

    def _create_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create message structure for API request."""
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
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]

    def _process_streaming_response(self, response) -> str:
        """Process streaming response, capturing valid JSON."""
        buffer = ""
        in_json = False
        json_depth = 0

        try:
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        if '{' in content and not in_json:
                            in_json = True
                            start_pos = content.find('{')
                            content = content[start_pos:]

                        if in_json:
                            json_depth += content.count('{') - content.count('}')
                            buffer += content

                            if json_depth == 0:
                                break

            try:
                json_obj = json.loads(buffer)
                return json.dumps(json_obj)
            except json.JSONDecodeError:
                return ""

        except Exception:
            return ""

    def _parse_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse the AI response and extract form data."""
        try:
            if not ai_response:
                return {"message": "Empty response", "form_data": {"fields": []}}

            form_data = json.loads(ai_response)

            if not isinstance(form_data, dict):
                return {"message": "Invalid response format", "form_data": {"fields": []}}

            if "form_data" in form_data and "fields" in form_data["form_data"]:
                return form_data

            return {"message": "Missing required fields in response", "form_data": {"fields": []}}

        except json.JSONDecodeError as e:
            return {"message": f"JSON parsing error: {str(e)}", "form_data": {"fields": []}}
        except Exception as e:
            return {"message": f"Error processing response: {str(e)}", "form_data": {"fields": []}}


if __name__ == "__main__":
    client = DeepSeekClient()

    current_form = {"fields": []}
    print("\nDeepSeek Form Generator")
    print("Type 'show' to see current form, or 'quit' to exit.")

    while True:
        user_input = input("\nEnter form requirements: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Exiting DeepSeek Form Generator.")
            break

        if user_input.lower() == "show":
            print(json.dumps(current_form, indent=2)
                  if current_form["fields"] else "No form created yet.")
            continue

        response_data = client.generate_form(user_input, current_form)

        if "form_data" in response_data and response_data["form_data"] is not None:
            current_form = response_data["form_data"]
            print(json.dumps(current_form, indent=2))
        else:
            print(f"Error: {response_data.get('message', 'Unknown error')}")