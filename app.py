import streamlit as st
from streamlit_option_menu import option_menu

from src.client.page import home, chat, data, setting

st.set_page_config(page_title="SQL Helper", page_icon="💬", layout="wide")

page_names_to_funcs = {
    "Home": home.render_page,
    "Chat": chat.render_page,
    "Data": data.render_page,
    "Setting": setting.render_page,
}

with st.sidebar:
    page_name = option_menu(
        menu_title="Menu",
        options=list(page_names_to_funcs.keys()),
        icons=["house", "search", "list-task", "gear"],
        menu_icon="app-indicator",
        default_index=0,
        styles={
            "container": {"padding": "5!important"},
            "icon": {"color": "orange", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left"},
        }
    )

page_names_to_funcs[page_name]()
