# import streamlit as st
# import json, os
# from dotenv import load_dotenv
# from openai import OpenAI  # DeepSeek uses OpenAI-compatible API
# from pydantic import BaseModel, ValidationError
# from typing import List, Optional
#
# # TODO: Not implemented yet: api server down
#
# load_dotenv()
# # Configure DeepSeek API
# client = OpenAI(
#     api_key=os.getenv("API_KEY"),
#     base_url="https://api.deepseek.com/v1"  # Verify latest API endpoint
# )
#
#
# class FormField(BaseModel):
#     type: str  # text, email, number, multiple_choice
#     label: str
#     required: bool = False
#     options: Optional[List[str]] = None
#     validation: Optional[dict] = None
#
#
# def parse_with_deepseek(prompt: str) -> dict:
#     """Use DeepSeek-R1 to extract form field details"""
#     system_prompt = """Extract form field details from the user's request. Return JSON with:
#     - "type" (text, email, number, multiple_choice)
#     - "label" (field label/question)
#     - "required" (true/false)
#     - "options" (if multiple_choice)
#     - "validation" (e.g., min_length, max_length, regex)
#
#     Example output:
#     {"type": "email", "label": "Email Address", "required": true}
#     """
#
#     response = client.chat.completions.create(
#         model="deepseek-r1",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.1,
#         response_format={"type": "json_object"}
#     )
#
#     return json.loads(response.choices[0].message.content)
#
#
# def validate_field(field_data: dict) -> FormField:
#     """Validate using Pydantic model"""
#     return FormField(**field_data)
#
#
# # Streamlit UI
# st.title("AI Form Builder with DeepSeek-R1")
#
# if "form_fields" not in st.session_state:
#     st.session_state.form_fields = []
#
# if prompt := st.chat_input("Describe a form field (e.g. 'Add required email field'):"):
#     try:
#         # Process with DeepSeek
#         raw_field = parse_with_deepseek(prompt)
#         validated_field = validate_field(raw_field)
#
#         # Add to form structure
#         st.session_state.form_fields.append(validated_field.dict())
#         st.success(f"Added {validated_field.type} field: {validated_field.label}")
#     except ValidationError as e:
#         st.error(f"Validation error: {str(e)}")
#     except json.JSONDecodeError:
#         st.error("Failed to parse DeepSeek response")
#
# # Display current form
# st.divider()
# st.subheader("Current Form Structure")
#
# if st.session_state.form_fields:
#     # Interactive form preview
#     for field in st.session_state.form_fields:
#         with st.container(border=True):
#             st.markdown(f"**{field['label']}** ({field['type']})")
#
#             if field["type"] == "text":
#                 st.text_input("", key=field["label"])
#             elif field["type"] == "email":
#                 st.text_input("", type="email", key=field["label"])
#             elif field["type"] == "multiple_choice":
#                 st.radio("", options=field["options"], key=field["label"])
#
#     # JSON export
#     st.divider()
#     st.subheader("JSON Output")
#     st.code(json.dumps(st.session_state.form_fields, indent=2))
# else:
#     st.info("No fields added yet. Start describing your form!")
#
# # Reset button
# if st.button("Reset Form"):
#     st.session_state.form_fields = []
#     st.rerun()
