import hashlib
import uuid
from typing import Union

import pandas as pd

from src.client.controller.common import get_vector_store


def get_all_ddl() -> pd.DataFrame:
    vector_store = get_vector_store()
    return vector_store.get_all_ddl()


def create_ddl(table_name: str, ddl: str, summary: str) -> str:
    vector_store = get_vector_store()
    return vector_store.add_ddl(table_name, ddl, summary)


def update_ddl():
    vector_store = get_vector_store()
    pass


def delete_ddl(id: str) -> None:
    vector_store = get_vector_store()
    return vector_store.delete_ddl(id)


def get_all_sql() -> pd.DataFrame:
    vector_store = get_vector_store()
    return vector_store.get_all_sql()


def create_sql(sql_alias: str, question: str, sql: str) -> str:
    vector_store = get_vector_store()
    return vector_store.add_sql(sql_alias, question, sql)


def update_sql():
    vector_store = get_vector_store()
    pass


def delete_sql(id: str) -> None:
    vector_store = get_vector_store()
    return vector_store.delete_sql(id)


def get_all_doc() -> pd.DataFrame:
    vector_store = get_vector_store()
    return vector_store.get_all_doc()


def create_doc(doc_name: str, doc: str) -> str:
    vector_store = get_vector_store()
    return vector_store.add_doc(doc_name, doc)


def update_doc():
    vector_store = get_vector_store()
    pass


def delete_doc(id: str) -> None:
    vector_store = get_vector_store()
    return vector_store.delete_doc(id)


def generate_uuid(content: Union[str, bytes]) -> str:
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    elif isinstance(content, bytes):
        content_bytes = content
    else:
        raise ValueError(f"Content type {type(content)} not supported !")

    hash_object = hashlib.sha256(content_bytes)
    hash_hex = hash_object.hexdigest()
    namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
    content_uuid = str(uuid.uuid5(namespace, hash_hex))

    return content_uuid
