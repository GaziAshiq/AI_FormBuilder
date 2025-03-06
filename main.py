import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from ai_server import AIClient
from form_generator import (
    generate_form_structure,
    process_ai_response,
    FIELD_TYPE_MAPPING,
    create_validation_rules
)
from spacy_form_processor import process_input

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global form state
class FormState:
    def __init__(self):
        self.current_form = {"fields": []}
        self.form_structure = None  # To store the complete form structure

    def update_form(self, form_data: Dict):
        """Update both the basic form and generated structure"""
        self.current_form = form_data
        self.form_structure = generate_form_structure(form_data)

form_state = FormState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize form state on startup"""
    global form_state
    form_state = FormState()
    yield

app = FastAPI(
    title="Form Generator API",
    description="API for generating dynamic forms based on user input",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize AI client
ai_client = AIClient(use_ollama=True)

class FormField(BaseModel):
    name: str
    label: str
    type: str
    required: bool = False
    options: Optional[List[Dict[str, str]]] = None

class FormData(BaseModel):
    fields: List[FormField]

class UserInput(BaseModel):
    input_text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user input describing the form field"
    )
    current_form: Optional[Dict[str, Any]] = None

class FormResponse(BaseModel):
    message: str
    form_data: FormData

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Form Generator API is running"}

@app.get("/form", response_model=FormResponse)
def get_form():
    """Get the current form state"""
    return {
        "message": "Current form retrieved",
        "form_data": form_state.current_form
    }

@app.post("/form/reset")
def reset_form():
    """Reset the form to empty state"""
    form_state.current_form = {"fields": []}
    return {
        "message": "Form reset successfully",
        "form_data": form_state.current_form
    }

@app.post("/generate-form", response_model=FormResponse)
async def generate_form(user_input: UserInput):
    """Generate a form based on user input using AI processing"""
    try:
        logger.info(f"Generating form for input: {user_input.input_text}")

        current_form = user_input.current_form or form_state.current_form

        # Get AI response
        ai_response = ai_client.fetch_chat_response(
            user_input.input_text,
            current_form
        )

        # Process AI response
        form_data = process_ai_response(ai_response)
        if not form_data:
            raise HTTPException(
                status_code=400,
                detail="Failed to generate form structure"
            )

        # Update global form state with both basic form and structure
        form_state.update_form(form_data)

        return {
            "message": "Form generated successfully",
            "form_data": form_data
        }

    except Exception as e:
        logger.error(f"Error generating form: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/form/structure")
async def get_form_structure():
    """Get the complete form structure including validation rules"""
    if not form_state.form_structure:
        form_state.form_structure = generate_form_structure(form_state.current_form)
    
    return {
        "message": "Form structure retrieved",
        "structure": form_state.form_structure
    }

@app.put("/form/field")
async def update_field(field_name: str, field_data: FormField):
    """Update a specific field in the form"""
    try:
        fields = form_state.current_form["fields"]
        for i, field in enumerate(fields):
            if field["name"] == field_name:
                # Add validation rules based on field type
                validation_rules = create_validation_rules(
                    field_data.type,
                    field_data.name
                )
                
                # Update field with validation
                field_dict = field_data.dict()
                field_dict["validation"] = validation_rules
                fields[i] = field_dict
                
                # Regenerate form structure
                form_state.update_form(form_state.current_form)
                
                return {
                    "message": f"Field '{field_name}' updated successfully",
                    "form_data": form_state.current_form
                }
        
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found"
        )

    except Exception as e:
        logger.error(f"Error updating field: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating field: {str(e)}"
        )

@app.delete("/form/field/{field_name}")
async def delete_field(field_name: str):
    """Delete a field from the form"""
    try:
        fields = form_state.current_form["fields"]
        form_state.current_form["fields"] = [
            f for f in fields if f["name"] != field_name
        ]
        return {
            "message": f"Field '{field_name}' deleted successfully",
            "form_data": form_state.current_form
        }

    except Exception as e:
        logger.error(f"Error deleting field: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting field: {str(e)}"
        )

@app.post("/generate-form/spacy")
def generate_form_spacy(user_input: UserInput):
    """
    Generate a form using the original Spacy implementation.
    This endpoint is kept for comparison and testing purposes.
    """
    try:
        form_data = process_input(user_input.input_text, user_input.current_form)
        return {
            "message": "Form updated successfully (Spacy)!",
            "form_data": form_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/field-types")
async def get_field_types():
    """Get available field types and their mappings"""
    return {
        "message": "Field types retrieved",
        "types": FIELD_TYPE_MAPPING
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
