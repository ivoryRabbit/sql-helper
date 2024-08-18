import streamlit as st

from src.client.controller.common import get_vector_store, get_assistant


def render_page() -> None:
    st.title("Hello")

    with st.spinner(text="Load models..."):
        get_vector_store()
        get_assistant()
