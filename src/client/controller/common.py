import streamlit as st

from src.client.controller.setting import OPENAI
from src.core.assistant.openai import OpenAIAssistant
from src.core.interface.assistant import Assistant
from src.core.interface.vector_store import VectorStore
from src.core.vector_store.chromadb import ChromaDBVectorStore


@st.cache_resource(ttl=3600)
def get_vector_store() -> VectorStore:
    return ChromaDBVectorStore(path="/tmp/.chromadb")


@st.cache_resource(ttl=3600)
def get_assistant() -> Assistant:
    return OpenAIAssistant(api_key=OPENAI.api_key, model=OPENAI.model_name)