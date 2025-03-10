"""
module to interact with the Gemini API (migrated to google.generativeai)
"""
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from utils.constants import instruction

load_dotenv()


def _create_prompt(user_input: str, current_form: dict) -> str:
    """
    Creates a formatted prompt for the Generative AI model.

    Args:
        user_input (str): The user's natural language request about form creation/modification
        current_form (dict): The current state of the form with all fields and properties

    Returns:
        str: A formatted prompt string ready to be sent to the model
    """
    prompt_template = f"""{instruction}
        Current form: {json.dumps(current_form)}\nUser input: {user_input}"""

    return prompt_template


def _parse_response(ai_response: str) -> dict:
    """
    Parses the JSON response from the Gemini model.

    Cleans the response text by removing markdown code block symbols and
    parses it into a Python dictionary. Handles various error cases.

    Args:
        ai_response (str): The raw text response from the AI model

    Returns:
        dict: The parsed response containing form data or error information
    """
    cleaned_response = ai_response.strip().lstrip(
        '`').lstrip('json').lstrip().rstrip('`')
    try:
        form_data = json.loads(cleaned_response)
        if "form_data" in form_data and "fields" in form_data["form_data"]:
            return form_data["form_data"]
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing Gemini response (JSONDecodeError): {e}")
        return {"message": "Error: Invalid JSON response from the model.", "form_data": {"fields": []}}
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {"message": f"An error occurred: {e}", "form_data": {"fields": []}}


class GenerativeAIClient:
    """
    Client class to interact with the Google Generative AI API.

    This class manages the connection to Google's generative AI model,
    maintains chat history, and handles form generation requests.
    """

    def __init__(self):
        """
        Initializes the Gemini client.

        Sets up the API connection using the configured API key and
        initializes a chat session with the specified model
        """
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.chat = self.model.start_chat(history=[])

    def generate_form(self, prompt_input: str, current_form: dict = None) -> dict:
        """
        Generates or updates a form based on user input.

        Sends a constructed prompt to the AI model and processes the response
        to return a structured form definition or error message.

        Args:
            prompt_input (str): The user's input describing the form requirements.
            current_form (dict, optional): The current form structure. Defaults to None.

        Returns:
            dict: The generated or updated form data, or an error message.
        """
        if current_form is None:
            current_form = {"fields": []}

        try:
            dynamic_prompt = _create_prompt(prompt_input, current_form)
            response = self.chat.send_message(dynamic_prompt)
            return _parse_response(response.text)
        except Exception as e:
            return {
                "message": f"Error: {str(e)}",
                "form_data": {"fields": []}
            }


if __name__ == "__main__":
    client = GenerativeAIClient()

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

        response_data = client.generate_form(user_input, current_form)
        if "form_data" in response_data and response_data["form_data"] is not None:
            print(json.dumps(response_data, indent=2))
            current_form = response_data["form_data"]
        else:
            print(json.dumps(response_data, indent=2))
