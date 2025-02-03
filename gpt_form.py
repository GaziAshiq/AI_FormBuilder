import os

from openai import OpenAI
import json

from dotenv import load_dotenv

# TODO: Not implemented yet: api server down

load_dotenv()

# Set your OpenAI API key
# openai.api_key = os.getenv("API_KEY")

client = OpenAI(api_key=os.getenv("API_KEY"), base_url="https://api.deepseek.com/beta")


def process_input_with_chatgpt(input_text):
    prompt = f"""
    I need you to generate a JSON structure for a dynamic form field based on the following user input. The JSON should contain the form field's name, type, required status, and options (if applicable).

    Example JSON structure:
    {{
        "Name": "name",
        "DataElementTypeId": "1",
        "IsRequired": true,
        "DisplayText": "Name",
        "DataElementColumnName": "name",
        "IsFixed": false,
        "DataElementOptions": null
    }}

    User input: "{input_text}"
    """

    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages,
        stream=True
    )

    response = openai.Completion.create(
        engine="gpt-3.5-turbo",  # You can use gpt-3.5 or gpt-4
        prompt=prompt,
        max_tokens=150,
        temperature=0.7,
        n=1,
        stop=["\n"]
    )

    return response.choices[0].text.strip()

def create_form_from_input(user_input):
    # Process the input using ChatGPT
    processed_json = process_input_with_chatgpt(user_input)

    # You may need to refine or parse the output to handle the full JSON structure
    return json.loads(processed_json)  # Return the structured JSON

# Example User Inputs
user_inputs = [
    "Create a text field for name",
    "Add a dropdown for gender with options Male, Female, Other",
    "Make the name field optional"
]

# Process and generate the form fields based on input
form_data = []
for user_input in user_inputs:
    field = create_form_from_input(user_input)
    form_data.append(field)

# Print the resulting JSON data
print(json.dumps(form_data, indent=2))
