import streamlit as st

from src.core.interface.vector_store import VectorStore
from src.core.vector_store.chromadb import ChromaDBVectorStore


@st.cache_resource(ttl=3600)
def get_vector_store() -> VectorStore:
    return ChromaDBVectorStore(path="/tmp/.chromadb")
