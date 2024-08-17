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
    return vector_store.add_sql(question, sql)


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
    return vector_store.add_doc(doc)


def update_doc():
    vector_store = get_vector_store()
    pass


def delete_doc(id: str) -> None:
    vector_store = get_vector_store()
    return vector_store.delete_doc(id)
