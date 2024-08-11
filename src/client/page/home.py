import streamlit as st

from src.client.resource import OPENAI


def render_page() -> None:
    st.title("Hi")
    st.markdown("WIP")
    st.markdown(OPENAI.api_key)
