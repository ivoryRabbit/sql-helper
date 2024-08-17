import pandas as pd

from src.core.interface.vector_store import VectorStore


class PGVectorStore(VectorStore):
    def add_ddl(self, ddl: str, **kwargs) -> str:
        pass

    def add_doc(self, doc: str, **kwargs) -> str:
        pass

    def add_sql(self, question: str, sql: str, **kwargs) -> str:
        pass

    def get_related_ddl(self, question: str, **kwargs) -> list:
        pass

    def get_related_doc(self, question: str, **kwargs) -> list:
        pass

    def get_related_sql(self, question: str, **kwargs) -> list:
        pass

    def get_all_data(self, **kwargs) -> pd.DataFrame:
        pass

    def remove_training_data(self, id: str, **kwargs) -> bool:
        pass
