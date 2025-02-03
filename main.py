from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from form_processor import process_input
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Form Generator API",
    description="API for generating dynamic forms based on user input",
    version="1.0.0"
)


# Input schema with validation
class UserInput(BaseModel):
    input_text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user input describing the form field"
    )


class FormField(BaseModel):
    name: str
    type: str
    required: bool = False

class FormData(BaseModel):
    fields: list[FormField] = list

    class Config:
        validate_assignment = True

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, dict):
            return cls(**value)
        return value


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
