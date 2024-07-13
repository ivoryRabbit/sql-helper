from abc import ABC, abstractmethod

import pandas as pd


class VectorStore(ABC):
    @abstractmethod
    def generate_embedding(self, text: str, **kwargs) -> list[float]:
        pass

    @abstractmethod
    def add_ddl(self, ddl: str, **kwargs) -> str:
        pass

    @abstractmethod
    def add_doc(self, doc: str, **kwargs) -> str:
        pass

    @abstractmethod
    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        pass

    @abstractmethod
    def get_related_ddl(self, question: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_related_doc(self, question: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_all_data(self, **kwargs) -> pd.DataFrame:
        pass

    @abstractmethod
    def remove_training_data(self, id: str, **kwargs) -> None:
        pass
