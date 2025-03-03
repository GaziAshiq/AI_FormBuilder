import json
import streamlit as st
from api.gemini_client import GeminiClient
from api.deepseek_client import DeepSeekClient
from api.generativeai_client import GeminiClient as GenerativeAIClient


def display_system_alert(message, alert_type="success"):
    """
    Display a system alert.
    Args:
        message: The message to display
        alert_type: Type of alert (success, warning, error, info)
    """
    # Define color schemes for different alert types
    color_schemes = {
        "success": {"bg": "#d4edda", "text": "#155724", "border": "#c3e6cb", "icon": "✅"},
        "warning": {"bg": "#fff3cd", "text": "#856404", "border": "#ffeeba", "icon": "⚠️"},
        "error": {"bg": "#f8d7da", "text": "#721c24", "border": "#f5c6cb", "icon": "❌"},
        "info": {"bg": "#cce5ff", "text": "#004085", "border": "#b8daff", "icon": "ℹ️"}
    }

    scheme = color_schemes.get(alert_type, color_schemes["info"])

    # Place the alert at the top of the main content area with smaller font
    st.markdown(f"""
    <div style="padding: 0.75rem; background-color: {scheme['bg']}; color: {scheme['text']};
                border-radius: 0.5rem; font-size: 1rem; text-align: center;
                margin: 0.5rem 0; border: 1px solid {scheme['border']}; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <strong>{scheme['icon']} {message}</strong>
    </div>
    """, unsafe_allow_html=True)


def app():
    st.set_page_config(page_title="Form Generator", page_icon="🔮", layout="wide")
    st.title("AI Form Generator")
    st.write("This app generates a form based on user input.")
    st.markdown("---")

    # Create a container for alerts at the top
    alert_container = st.container()

    # Model selection in sidebar
    with st.sidebar:
        selected_model = st.selectbox(
            "Select AI Model",
            ["Gemini", "GenerativeAI", "DeepSeek:R1"],
            index=0
        )
        st.caption(f"Currently using: {selected_model}")

    # Initialize session state
    if "form_data" not in st.session_state:
        st.session_state.form_data = {"fields": []}

    if "selected_model" not in st.session_state or st.session_state.selected_model != selected_model:
        st.session_state.selected_model = selected_model
        # Reset form when changing models
        st.session_state.form_data = {"fields": []}

    # Initialize the appropriate client based on selection
    if selected_model == "Gemini":
        client = GeminiClient()
    elif selected_model == "GenerativeAI":
        client = GenerativeAIClient()
    else:  # DeepSeek
        client = DeepSeekClient()

    # Display current model info
    st.caption(f"Powered by {selected_model} AI")

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
        col1, col2, col3 = st.columns([3, 3, 2])
        with col1:
            if st.button("Generate", type="primary", disabled=not user_input):
                with st.spinner(f"Generating form using {selected_model}..."):
                    try:
                        output = client.generate_form(
                            user_input, st.session_state.form_data)
                        if "form_data" in output:
                            output = output["form_data"]

                        if output and "fields" in output:
                            st.session_state.form_data = output
                            # Using the alert container to display at the top
                            with alert_container:
                                display_system_alert("Form updated successfully!")
                        else:
                            with alert_container:
                                display_system_alert("Failed to update form.", "warning")
                    except Exception as e:
                        with alert_container:
                            display_system_alert(f"Error: {str(e)}", "error")

        with col2:
            if st.button("Show Current Form", type="secondary", disabled=not st.session_state.form_data.get("fields")):
                st.markdown("### Current Form")
                st.json(st.session_state.form_data)

        with col3:
            if st.button("Clear Form", type="tertiary", disabled=not st.session_state.form_data.get("fields")):
                st.session_state.form_data = {"fields": []}
                with alert_container:
                    display_system_alert("Form cleared successfully!", "info")

    # Display area
    if st.session_state.form_data.get("fields"):
        st.markdown("### Generated Form")
        st.json(st.session_state.form_data)
