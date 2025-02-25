"""
module to interact with the Gemini API
"""
import os
import json
from google import genai
from dotenv import load_dotenv
from utils.constants import instruction

load_dotenv()


def _create_prompt(user_input: str, current_form: dict) -> str:

    return f"{instruction}\nCurrent form: {json.dumps(current_form)}\nUser input: {user_input}"


def _parse_response(ai_response: str) -> dict:
    cleaned_response = ai_response.strip().lstrip(
        '`').lstrip('json').lstrip().rstrip('`')
    try:
        form_data = json.loads(cleaned_response)
        if "form_data" in form_data and "fields" in form_data["form_data"]:
            return form_data["form_data"]
        return {}
        # return form_data
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {}
        # return {"error": "invalid response structure"}


class GeminiClient:
    """
    Class to interact with the Gemini API
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash"

    def generate_form(self, prompt_input: str, current_form: dict = None) -> dict:
        """
        Generate a form based on user input
        """
        if current_form is None:
            current_form = {"fields": []}

        try:
            dynamic_prompt = _create_prompt(prompt_input, current_form)
            response = self.client.models.generate_content(
                model=self.model,
                contents=dynamic_prompt
            )
            return _parse_response(response.text)
        except Exception as e:
            return {
                "message": f"Error: {str(e)}",
                "form_data": {"fields": []}
            }


if __name__ == "__main__":
    client = GeminiClient()

    current_form = {"fields": []}
    print("\nGemini Form Generator")
    print("Type 'show' to see current form, or 'quit' to exit.")
    while True:
        user_input = input("\nEnter form requirements: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Exiting Gemini Form Generator.")
            break
        if user_input.lower() == "show":
            print(json.dumps(current_form, indent=2)
                  if current_form["fields"] else "No form created yet.")
            continue

        form_data = client.generate_form(user_input, current_form)
        print(json.dumps(form_data, indent=2))
        current_form = form_data
