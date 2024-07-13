from src.agent.sql_agent import SQLAgent
from src.core.chat.openai import OpenAIChat
from src.core.interface.vector_store import VectorStore


class OpenAISQLAgent(OpenAIChat, SQLAgent):
    def __init__(self, vector_store: VectorStore, openai_api_key=None, openai_model=None, config=None):
        SQLAgent.__init__(self, vector_store=vector_store, config=config)
        OpenAIChat.__init__(self, api_key=openai_api_key, model=openai_model, config=config)
