from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from form_processor import process_input

app = FastAPI()


# Input schema for the API
class UserInput(BaseModel):
    input_text: str


# Initialize an empty form JSON structure
form_data = {"fields": []}


@app.get("/form")
def get_form():
    """
    Get the current form data.
    """
    return form_data


@app.post("/generate-form")
def generate_form(user_input: UserInput):
    """
    Generate a form based on user input.

    Args:
        user_input (UserInput): The user input describing the form field.

    Returns:
        dict: The updated form data structure.
    """
    global form_data

    try:
        form_data = process_input(user_input.input_text, form_data)
        return {"message": "Form updated successfully!", "form_data": form_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
