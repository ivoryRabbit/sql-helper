from glob import glob

import streamlit as st

from src.client.controller.common import get_vector_store, get_assistant
from src.utils import read_sql


def render_page() -> None:
    st.title("Hello")

    file_names = ["movies.sql", "users.sql", "ratings.sql"]

    for file_name in file_names:
        sql = read_sql(f"./resource/sql/{file_name}")
        st.code(sql, language="sql")

    with st.spinner(text="Load models..."):
        get_vector_store()
        get_assistant()
