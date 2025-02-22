import logging
from functools import lru_cache
from dotenv import load_dotenv

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_client() -> AsyncOpenAI:
    load_dotenv()
    return AsyncOpenAI()
