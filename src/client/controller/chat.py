import streamlit as st

from src.client.controller.common import get_vector_store, get_assistant
from src.core.sql_agent import SQLAgent


@st.cache_resource(ttl=3600)
def setup_agent():
    assistant = get_assistant()
    vector_store = get_vector_store()
    return SQLAgent(assistant, vector_store, print_log=True)


@st.cache_data(show_spinner="Generating sample questions ...")
def generate_suggestions_cached():
    agent = setup_agent()
    return agent.generate_suggestions()


@st.cache_data(show_spinner="Generating SQL query ...")
def generate_sql_cached(question: str):
    agent = setup_agent()
    return agent.generate_sql(question=question)


@st.cache_data(show_spinner="Checking for valid SQL ...")
def is_sql_valid_cached(sql: str):
    agent = setup_agent()
    return agent.is_sql_valid(sql=sql)


@st.cache_data(show_spinner="Generating followup questions ...")
def generate_followup_cached(question: str, sql: str):
    agent = setup_agent()
    return agent.generate_followup_questions(question=question, sql=sql)
