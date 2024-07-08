from abc import ABC

import pandas as pd
from vanna.base import VannaBase


class PGVector(VannaBase, ABC):
    def add_ddl(self, ddl: str, **kwargs) -> str:
        pass

    def add_documentation(self, doc: str, **kwargs) -> str:
        pass

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        pass

    def get_related_ddl(self, question: str, **kwargs) -> list:
        pass

    def get_related_documentation(self, question: str, **kwargs) -> list:
        pass

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        pass

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        pass

    def remove_training_data(id: str, **kwargs) -> bool:
        pass
