from functools import lru_cache
from typing import Optional

from sqlalchemy import create_engine, Engine


_engine: Optional[Engine] = None


def init_client() -> None:
    global _engine
    _engine = create_engine(
        url="trino://admin@localhost:543/hive/movielens",
        echo=True,
    )


@lru_cache
def get_client() -> Engine:
    global _engine
    assert _engine is not None
    return _engine


def close() -> None:
    global _engine
    _engine = None
