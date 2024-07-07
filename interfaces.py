from mixin.chromadb_vector_store import ChromaDBVectorStore
from mixin.vannadb_vector_store import VannaDBVectorStore
from mixin.openai_chat import OpenAIChat


class ChromaDB(ChromaDBVectorStore, OpenAIChat):
    def __init__(
        self, path=None, openai_api_key=None, openai_model_name=None, config=None,
    ):
        ChromaDBVectorStore.__init__(self, path=path, config=config)
        OpenAIChat.__init__(self, api_key=openai_api_key, model_name=openai_model_name, config=config)


class VannaDB(VannaDBVectorStore, OpenAIChat):
    def __init__(
        self, vanna_api_key=None, vanna_model_name=None, openai_api_key=None, openai_model_name=None, config=None,
    ):
        VannaDBVectorStore.__init__(self, api_key=vanna_api_key, model_name=vanna_model_name, config=config)
        OpenAIChat.__init__(self, api_key=openai_api_key, model_name=openai_model_name, config=config)
