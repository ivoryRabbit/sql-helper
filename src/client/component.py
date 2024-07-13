import streamlit as st

from src.agent.openai_sql_agent import OpenAISQLAgent
from src.core.vector_store.chromadb import ChromaDBVectorStore


@st.cache_resource(ttl=3600)
def setup_agent():
    vector_store = ChromaDBVectorStore(path="../../.chromadb")

    agent = OpenAISQLAgent(
        vector_store,
        openai_api_key=st.secrets.get("OPENAI_API_KEY"),
        openai_model=st.secrets.get("OPENAI_MODEL_NAME"),
    )
    return agent


@st.cache_data(show_spinner="Generating sample questions ...")
def generate_questions_cached():
    agent = setup_agent()
    return agent.generate_questions()


@st.cache_data(show_spinner="Generating SQL query ...")
def generate_sql_cached(question: str):
    agent = setup_agent()
    return agent.generate_sql(question=question, allow_llm_to_see_data=True)


@st.cache_data(show_spinner="Checking for valid SQL ...")
def is_sql_valid_cached(sql: str):
    agent = setup_agent()
    return agent.is_sql_valid(sql=sql)


@st.cache_data(show_spinner="Generating followup questions ...")
def generate_followup_cached(question, sql, df):
    agent = setup_agent()
    return agent.generate_followup_questions(question=question, sql=sql, df=df)


@st.cache_data(show_spinner="Generating summary ...")
def generate_summary_cached(question, df):
    agent = setup_agent()
    return agent.generate_summary(question=question, df=df)
