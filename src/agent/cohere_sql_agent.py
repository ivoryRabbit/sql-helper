from src.agent.sql_agent import SQLAgent
from src.core.chat.cohere import CohereChat
from src.core.interface.vector_store import VectorStore


class CohereSQLAgent(CohereChat, SQLAgent):
    def __init__(self, vector_store: VectorStore, cohere_api_key=None, cohere_model=None, config=None):
        SQLAgent.__init__(self, vector_store=vector_store, config=config)
        CohereChat.__init__(self, api_key=cohere_api_key, model=cohere_model, config=config)
