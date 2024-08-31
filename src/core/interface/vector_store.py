from abc import ABC, abstractmethod
from typing import List, Dict

import pandas as pd


class VectorStore(ABC):
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def add_ddl(self, id: str, ddl: str, summary: str) -> str:
        pass

    @abstractmethod
    def add_doc(self, id: str, doc: str) -> str:
        pass

    @abstractmethod
    def add_sql(self, id: str, question: str, sql: str) -> str:
        pass

    # @abstractmethod
    # def add_ddl_bulk(self, data: List[Dict[str, str]]) -> str:
    #     pass
    #
    # @abstractmethod
    # def add_doc_bulk(self, data: List[Dict[str, str]]) -> str:
    #     pass
    #
    # @abstractmethod
    # def add_sql_bulk(self, data: List[Dict[str, str]]) -> str:
    #     pass

    @abstractmethod
    def get_all_ddl(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_all_doc(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_all_sql(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def update_ddl(self, id: str, ddl: str, summary: str) -> str:
        pass

    @abstractmethod
    def update_doc(self, id: str, doc: str) -> str:
        pass

    @abstractmethod
    def update_sql(self, id: str, question: str, sql: str) -> str:
        pass

    @abstractmethod
    def delete_ddl(self, id: str) -> None:
        pass

    @abstractmethod
    def delete_doc(self, id: str) -> None:
        pass

    @abstractmethod
    def delete_sql(self, id: str) -> None:
        pass

    @abstractmethod
    def get_related_ddl(self, question: str, n_results: int) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def get_related_doc(self, question: str, n_results: int) -> List[str]:
        pass

    @abstractmethod
    def get_related_sql(self, question: str, n_results: int) -> List[Dict[str, str]]:
        pass
