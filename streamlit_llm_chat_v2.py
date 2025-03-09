import streamlit as st
from api.deepseek_client import DeepSeekClient
from api.gemini_client import GeminiClient


def app():
    st.set_page_config(page_title="Form Generator", page_icon="🔮", layout="centered")
    st.title("Form Generator")
    st.write("This app generates a form based on user input.")

    # Model selection
    model = st.sidebar.selectbox("Select Model", ["DeepSeek", "Gemini"])
    st.caption(f"Powered by {model} AI")
    st.markdown("---")

    # Initialize client based on selection
    if model == "DeepSeek":
        client = DeepSeekClient()
    else:
        client = GeminiClient()

    # Initialize form data
    if "form_data" not in st.session_state:
        st.session_state.form_data = {"fields": []}

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Display current form
    if st.session_state.form_data.get("fields"):
        with st.expander("Current Form"):
            st.json(st.session_state.form_data)

    # Accept user input
    if prompt := st.chat_input("Describe your form requirements..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner(f"Generating form with {model}..."):
                try:
                    # Generate form response
                    response = client.generate_form(prompt, st.session_state.form_data)

                    # Extract message and form data
                    message = response.get("message", "Form updated successfully!")
                    form_data = response.get("form_data", {"fields": []})

                    # Update form data
                    if form_data and "fields" in form_data:
                        st.session_state.form_data = form_data
                        st.markdown(f"✅ {message}")
                        st.json(form_data)
                    else:
                        st.markdown(f"❌ Failed to update form: {message}")
                except Exception as e:
                    st.markdown(f"❌ Error: {str(e)}")

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": message})


if __name__ == "__main__":
    app()