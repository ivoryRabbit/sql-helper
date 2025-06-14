from functools import lru_cache
from typing import Optional

from compoent.vector_db import VectorDB


_vector_db: Optional[VectorDB] = None


def init_client() -> None:
    global _vector_db
    _vector_db = VectorDB(
        path="/tmp/sql-helper/vector_db"
    )


@lru_cache
def get_client() -> VectorDB:
    global _vector_db
    assert _vector_db is not None
    return _vector_db


def close() -> None:
    global _vector_db
    _vector_db = None
