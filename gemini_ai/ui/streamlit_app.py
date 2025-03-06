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
    # Initialize session state FIRST, before any access to these variables
    if "form_data" not in st.session_state:
        st.session_state.form_data = {"fields": []}

    if "comparison_results" not in st.session_state:
        st.session_state.comparison_results = {}

    if "text_input_submitted" not in st.session_state:
        st.session_state.text_input_submitted = False

    if "model_forms" not in st.session_state:
        st.session_state.model_forms = {
            "GenerativeAI": {"fields": []},
            "Gemini": {"fields": []},
            "DeepSeek:R1": {"fields": []}
        }

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "GenerativeAI"

    # Now set up the page
    st.set_page_config(page_title="Form Generator", page_icon="🔮", layout="wide")
    st.title("AI Form Generator")
    st.write("This app generates a form based on user input.")
    st.markdown("---")

    # Create a container for alerts at the top
    alert_container = st.container()

    if "form_updated" not in st.session_state:
        st.session_state.form_updated = False

    # Model selection in sidebar
    with st.sidebar:
        selected_model = st.selectbox(
            "Select AI Model",
            ["GenerativeAI", "Gemini", "DeepSeek:R1"],
            index=0
        )
        st.caption(f"Currently using: {selected_model}")
        st.markdown("""**Form View**""")
        # Display current generated output
        if st.session_state.form_data and st.session_state.form_data.get("fields"):
            fields = st.session_state.form_data.get("fields", [])
            field_count = len(fields)

            with st.expander(f"View Current Form Structure ({field_count} fields)", expanded=True):
                for i, field in enumerate(fields):
                    field_type = field.get("type", "unknown")
                    field_label = field.get("label", "Unlabeled")
                    field_name = field.get("name", "unnamed")
                    field_required = field.get("required", False)

                    # Type-specific icons
                    icons = {
                        "text": "📝", "number": "🔢", "radio": "⚪",
                        "dropdown": "🔽", "date": "📅", "file": "📎"
                    }
                    field_icon = icons.get(field_type, "❓")

                    # Field box with colored border based on required status
                    st.markdown(f"""
                            <div style="border-left: 3px solid {'#ff6b6b' if field_required else '#aaa'};
                                     padding-left: 10px; margin-bottom: 12px;">
                                <h4 style="margin:0">{i + 1}. {field_icon} {field_label}</h4>
                                <p style="margin:0; color:#666; font-size:0.9em">
                                    <span style="color:{'#ff4b4b' if field_required else '#777'}">
                                        {'⚠️ Required' if field_required else '◯ Optional'}
                                    </span> •
                                    <code>{field_type}</code> •
                                    <span style="font-family:monospace">name: {field_name}</span>
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

                    # Show options for dropdown and radio types
                    if field_type in ["dropdown", "radio"] and "options" in field:
                        options = field.get("options", [])
                        if options:
                            with st.container():
                                st.caption("Options:")
                                for opt in options[:5]:  # Limit to first 5 options
                                    st.markdown(f"• {opt.get('label', 'Unnamed')}")
                                if len(options) > 5:
                                    st.caption(f"...and {len(options) - 5} more options")
        else:
            st.caption("No form generated yet. Enter requirements above to create a form.")

    if "selected_model" in st.session_state and st.session_state.selected_model != selected_model:
        old_model = st.session_state.selected_model
        st.session_state.selected_model = selected_model
        st.session_state.form_data = {"fields": []}
        with alert_container:
            display_system_alert(f"Switched from {old_model} to {selected_model}. Form reset.", "info")

    # Initialize the appropriate client based on selection
    if selected_model == "Gemini":
        client = GeminiClient()
    elif selected_model == "GenerativeAI":
        client = GenerativeAIClient()
    else:  # DeepSeek
        client = DeepSeekClient()

    # Display current model info
    st.caption(f"Powered by {selected_model} AI")

    # Function to generate form
    def generate_form():
        if not user_input:
            return

        with st.spinner(f"Generating form using {selected_model}..."):
            try:
                # Get complete response from model
                response = client.generate_form(user_input, st.session_state.form_data)

                # Extract message from response
                message = response.get("message", "Form updated successfully!")

                # Extract form data
                form_data = response.get("form_data", response)

                if form_data and "fields" in form_data:
                    # Update the form data in session state
                    st.session_state.form_data = form_data
                    st.session_state.form_updated = True

                    # Display the model's message
                    with alert_container:
                        display_system_alert(message)

                    # Force a rerun to update the sidebar
                    st.rerun()
                else:
                    with alert_container:
                        display_system_alert("Failed to update form.", "warning")
            except Exception as e:
                with alert_container:
                    display_system_alert(f"Error: {str(e)}", "error")

    # Function to compare all models
    def compare_all_models():
        if not user_input:
            return

        # Initialize all clients
        clients = {
            "Gemini": GeminiClient(),
            "GenerativeAI": GenerativeAIClient(),
            "DeepSeek:R1": DeepSeekClient()
        }

        # Process with each client using their own persistent state
        for model_name, model_client in clients.items():
            with st.spinner(f"Generating with {model_name}..."):
                try:
                    # Use the model's own form state for continuity
                    current_model_form = st.session_state.model_forms.get(model_name, {"fields": []})

                    # Get complete response
                    response = model_client.generate_form(user_input, current_model_form)

                    # Extract message and form data while preserving the full structure
                    message = response.get("message", "Form updated successfully!")
                    form_data = response.get("form_data", response)

                    if form_data and "fields" in form_data:
                        # Update the model's state for future use
                        st.session_state.model_forms[model_name] = form_data
                        # Store both message and form_data in comparison results
                        st.session_state.comparison_results[model_name] = {
                            "message": message,
                            "form_data": form_data
                        }
                    else:
                        st.session_state.comparison_results[model_name] = {
                            "message": "Failed to generate form",
                            "form_data": {"fields": []},
                            "error": "Invalid response format"
                        }
                except Exception as e:
                    st.session_state.comparison_results[model_name] = {
                        "message": f"Error: {str(e)}",
                        "form_data": {"fields": []},
                        "error": str(e)
                    }

        with alert_container:
            display_system_alert("Comparison completed", "info")

    # Input area
    with st.container():
        user_input = st.text_area(
            "Describe your form requirements:",
            placeholder="Example: 'Please create a form that includes Name, Email address, "
                        "and Date of Birth.'\n\n"
                        "Add a field: 'add phone number field'\n"
                        "Require field: 'make email not required'\n"
                        "Remove fields: 'remove email field'\n\n"
                        "Press Ctrl+Enter to generate",
            height=150,
            key="user_input_area",
            on_change=generate_form if st.session_state.text_input_submitted else None
        )

        col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 1, 1])
        with col1:
            if st.button("Generate", type="primary", disabled=not user_input) or st.session_state.get(
                    "text_input_submitted"):
                # Reset the flag after handling
                if st.session_state.get("text_input_submitted"):
                    st.session_state.text_input_submitted = False
                generate_form()

        with col2:
            if st.button("Compare All Models", type="secondary", disabled=not user_input):
                compare_all_models()

        with col3:
            if st.button("Show Current Form", type="secondary", disabled=not st.session_state.form_data.get("fields")):
                st.markdown("### Current Form")
                st.json(st.session_state.form_data)

        with col4:
            if st.button("Clear Form", type="tertiary", disabled=not st.session_state.form_data.get("fields")):
                st.session_state.form_data = {"fields": []}
                with alert_container:
                    display_system_alert("Form cleared successfully!", "info")

        with col5:
            # Better condition to check for any model forms or comparison results
            has_any_data = bool(st.session_state.comparison_results) or \
                           (st.session_state.get("model_forms") and
                            any(bool(form.get("fields", [])) for form in st.session_state.model_forms.values()))

            if st.button("Clear All Forms", type="tertiary", disabled=not has_any_data):
                # Reset the current form
                st.session_state.form_data = {"fields": []}
                # Reset comparison results
                st.session_state.comparison_results = {}
                # Reset all model-specific forms
                st.session_state.model_forms = {
                    "Gemini": {"fields": []},
                    "GenerativeAI": {"fields": []},
                    "DeepSeek:R1": {"fields": []}
                }
                with alert_container:
                    display_system_alert("All forms cleared successfully!", "info")

    # Display area
    if st.session_state.form_data.get("fields"):
        st.markdown("### Generated Form")
        st.json(st.session_state.form_data)

    # Display comparison results if available
    if st.session_state.comparison_results:
        st.markdown("## Model Comparison")

        # Create columns for side-by-side comparison
        model_names = list(st.session_state.comparison_results.keys())
        cols = st.columns(len(model_names))

        # Display each model's output in its own column
        for i, model_name in enumerate(model_names):
            with cols[i]:
                st.markdown(f"### {model_name}")
                result = st.session_state.comparison_results[model_name]

                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    # Display the message first
                    if "message" in result:
                        st.success(result["message"])

                    # Then display the form data
                    form_data = result.get("form_data", {})
                    if form_data.get("fields"):
                        st.json(form_data)
                    else:
                        st.warning("No fields generated")
