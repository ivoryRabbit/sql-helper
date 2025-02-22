import logging
from functools import lru_cache
from typing import Optional

from temporalio.client import Client

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


async def init_client() -> None:
    global _client
    _client = await Client.connect("localhost:7233")


@lru_cache(maxsize=None)
def get_client() -> Client:
    global _client
    assert _client is not None
    return _client
