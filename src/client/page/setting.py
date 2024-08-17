import streamlit as st

from src.client.controller.setting import OPENAI, COHERE, CLAUDE


def render_page() -> None:
    st.title("Setting")

    assistants = {
        "OpenAI": OPENAI,
        "Cohere": COHERE,
        "Clause": CLAUDE
    }

    assistant_name = st.radio(
        "Which AI assistant would you like to use?",
        assistants,
    )

    with st.form("set_assistant"):
        assistant = assistants[assistant_name]

        api_key = st.text_input("API Key", value=assistant.api_key, type="password")
        model_name = st.text_input("API Key", value=assistant.model_name)
        is_submitted = st.form_submit_button("Submit", use_container_width=True)

        if is_submitted is True:
            assistant.api_key = api_key
            assistant.model_name = model_name
