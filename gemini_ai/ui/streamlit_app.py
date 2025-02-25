import json
import streamlit as st
from api.gemini_client import GeminiClient


def app():
    st.set_page_config(page_title="Form Generator", page_icon="🔮", layout="centered")
    st.title("Gemini AI Form Generator")
    st.write("This app generates a form based on user input.")
    st.caption("Powered by Gemini AI")
    st.markdown("---")

    # Initialize session state
    if "form_data" not in st.session_state:
        st.session_state.form_data = {"fields": []}

    client = GeminiClient()

    # Input area
    with st.container():
        user_input = st.text_area("Describe your form requirements:",
                                  placeholder="Example: 'Please create a form that includes Name, Email address, "
                                              "and Date of Birth.'\n\n"
                                              "Add a field: 'add phone number field'\n"
                                              "Require field: 'make email not required'\n"
                                              "Remove fields: 'remove email field'",
                                  height=150
                                  )
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            if st.button("Generate", type="primary", disabled=not user_input):
                with st.spinner("Generating form..."):
                    try:
                        output = client.generate_form(user_input, st.session_state.form_data)
                        if output.get("fields") is not None:
                            st.session_state.form_data = output
                            st.success("Form updated successfully!")
                        else:
                            st.warning("Failed to update form.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        with col2:
            if st.button("Show Current Form", type="secondary", disabled=not st.session_state.form_data.get("fields")):
                st.markdown("### Current Form")
                st.json(st.session_state.form_data)

        with col3:
            if st.button("Clear Form", type="tertiary", disabled=not st.session_state.form_data.get("fields")):
                st.session_state.form_data = {"fields": []}
                st.success("Form cleared successfully!")

    # Display area
    if st.session_state.form_data.get("fields"):
        st.markdown("### Generated Form")
        st.json(st.session_state.form_data)
