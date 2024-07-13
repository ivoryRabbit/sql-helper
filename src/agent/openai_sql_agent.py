from src.server.agent.sql_agent import SQLAgent
from src.server.service.vector_store.chromadb_mixin import ChromaDBVectorStore
from src.server.service.vector_store.openai_mixin import OpenAIChat


class OpenAISQLAgent(ChromaDBVectorStore, OpenAIChat, SQLAgent):
    def __init__(self, path=None, openai_api_key=None, openai_model_name=None, config=None):
        SQLAgent.__init__(self, config=config)
        ChromaDBVectorStore.__init__(self, path=path, config=config)
        OpenAIChat.__init__(self, api_key=openai_api_key, model_name=openai_model_name, config=config)