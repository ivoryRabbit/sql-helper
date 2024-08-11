import streamlit as st

from src.client.resource import OPENAI, COHERE, CLAUDE


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

        api_key = st.text_input("OpenAI API Key", value=assistant.api_key, type="password")
        submitted = st.form_submit_button("Submit", use_container_width=True)

        if submitted is True:
            assistant.api_key = api_key
