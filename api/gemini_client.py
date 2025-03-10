"""
module to interact with the Gemini API
"""
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from utils.constants import instruction

load_dotenv()


def _create_prompt(user_input: str, current_form: dict) -> str:
    return f"Current form: {json.dumps(current_form)}\nUser input: {user_input}"


def _parse_response(ai_response: str) -> dict:
    cleaned_response = ai_response.strip().lstrip(
        '`').lstrip('json').lstrip().rstrip('`')
    try:
        response_obj = json.loads(cleaned_response)
        if "form_data" in response_obj and "fields" in response_obj["form_data"]:
            return response_obj  # Return the full response including a message
        return {"message": "Invalid response format", "form_data": {"fields": []}}
    except json.JSONDecodeError as e:
        print(f"Error parsing response (JSONDecodeError): {e}")
        return {"message": "Error: Invalid JSON response from the model.", "form_data": {"fields": []}}
    except Exception as e:
        print(f"Error parsing response: {e}")
        return {"message": f"An error occurred: {e}", "form_data": {"fields": []}}


class GeminiClient:
    """
    Class to interact with the Gemini API
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.client = genai.Client(api_key=api_key)
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
                config=types.GenerateContentConfig(
                    system_instruction=instruction,
                    max_output_tokens=10000,
                    temperature=0.1
                ),
                contents=[dynamic_prompt]
            )
            response_text = response.candidates[0].content.parts[0].text
            return _parse_response(response_text)
        except Exception as e:
            print(f"Error generating form: {type(e).__name__} - {str(e)}")
            return {
                "message": f"Error: {type(e).__name__} - {str(e)}",
                "form_data": {"fields": []}
            }


if __name__ == "__main__":
    client = GeminiClient()

    current_form = {"fields": []}
    print("\nGemini Form Generator")
    print("Type 'show' to see current form, or 'quit' to exit.")
    # run_once = True
    while True:
        user_input = input("\nEnter form requirements: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Exiting Gemini Form Generator.")
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
        # run_once = False
