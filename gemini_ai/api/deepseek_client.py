import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from utils.constants import instruction
from dotenv import load_dotenv

load_dotenv()


class DeepSeekClient:
    """
    Client for interacting with DeepSeek API to generate form data.

    This class provides functionality to communicate with the DeepSeek AI model
    through the OpenAI client interface, specifically for generating and
    modifying form structures based on natural language requests.

    Attributes:
        api_key (str): API key for authenticating with DeepSeek
        client (OpenAI): Configured OpenAI client instance
        model (str): The DeepSeek model identifier to use
        system_prompt (str): Instructions for the AI model
    """

    def __init__(self):
        """
        Initialize the DeepSeek client with API configuration.

        Sets up the connection to DeepSeek's API using the OpenAI client library.
        Requires the DEEPSEEK_API_KEY environment variable to be set.

        Raises:
            ValueError: If the DEEPSEEK_API_KEY environment variable is not set
        """
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")

        # Configure OpenAI client to use DeepSeek API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/beta"
        )
        self.model = "deepseek-chat"
        self.system_prompt = instruction

    def generate_form(self, prompt_input: str, current_form: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a form based on user input using DeepSeek model.

        This method handles the complete workflow of form generation:
        1. Creating appropriate messages with context
        2. Sending the request to the DeepSeek API
        3. Processing the streaming response
        4. Parsing the response into a structured form

        Args:
            prompt_input (str): The user's natural language form requirements
            current_form (Optional[Dict[str, Any]]): The existing form structure to modify,
                                                    or None to create a new form

        Returns:
            Dict[str, Any]: Dictionary containing the generated form data or error information
                           with the structure: {"message": str, "form_data": Dict}
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
        """
        Create message structure for the API request.

        Formats the system prompt and user message based on whether we're modifying
        an existing form or creating a new one.

        Args:
            context (Dict[str, Any]): Dictionary containing the current form and user request

        Returns:
            List[Dict[str, str]]: List of message objects with role and content keys
        """
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
        """
        Process streaming response, capturing valid JSON.

        Handles chunked streaming responses from the API, detecting and
        extracting complete JSON objects by tracking opening and closing braces.

        Args:
            response: The streaming response iterator from the API call

        Returns:
            str: The complete JSON response as a string, or empty string if parsing fails
        """
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
        """
        Parse the AI response and extract form data.

        Validates the response format and ensures it contains the expected
        structure with form fields.

        Args:
            ai_response (str): The JSON string response from the AI model

        Returns:
            Dict[str, Any]: Dictionary containing the parsed form data or error information
                           with the structure: {"message": str, "form_data": Dict}
        """
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
