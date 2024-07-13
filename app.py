import streamlit as st
from streamlit_option_menu import option_menu

from src.client.page import home, openai, cohere, setting

st.set_page_config(page_title="SQL Helper", page_icon="💬", layout="wide")

page_names_to_funcs = {
    "Home": home.render_page,
    "OpenAI": openai.render_page,
    "Cohere": cohere.render_page,
    "Setting": setting.render_page,
}

with st.sidebar:
    page_name = option_menu(
        menu_title="Menu",
        options=list(page_names_to_funcs.keys()),
        icons=["house", "search", "search", "gear"],
        menu_icon="app-indicator",
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "25px"},
            "nav-link": {"font-size": "16px", "text-align": "left"},
            "nav-link-selected": {"background-color": "#02ab21"},
        }
    )

page_names_to_funcs[page_name]()
