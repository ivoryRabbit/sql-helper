import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingClient:
    MODEL_NAME = "all-MiniLM-L6-v2"
    DIMENSIONS = 384

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model '%s' ...", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded.")
        return self._model

    async def embed(self, text: str) -> list[float]:
        loop = asyncio.get_running_loop()
        model = self._get_model()
        result = await loop.run_in_executor(None, model.encode, text)
        return result.tolist()

    async def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []
        loop = asyncio.get_running_loop()
        model = self._get_model()
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            results = await loop.run_in_executor(None, model.encode, batch)
            all_embeddings.extend(results.tolist())
        return all_embeddings
