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
        user_input = st.text_area("Describe your form requirements:", height=100)
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Generate", type="primary"):
                if user_input:
                    st.session_state.form_data = client.generate_form(user_input, st.session_state.form_data)
        with col2:
            if st.button("Clear"):
                st.session_state.form_data = {"fields": []}

    # Display area
    if st.session_state.form_data.get("fields"):
        st.markdown("### Generated Form")
        st.json(st.session_state.form_data)