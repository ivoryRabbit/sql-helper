import json
from typing import List, Sequence

import chromadb
import pandas as pd
from chromadb import QueryResult
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from src.core.interface.vector_store import VectorStore


class ChromaDBVectorStore(VectorStore):
    def __init__(self, path: str, config=None):
        if config is None:
            config = {}

        _DEFAULT_EF = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        _DEFAULT_VSS = {"hnsw:space": "cosine"}

        self.embedding_function = config.get("embedding_function", _DEFAULT_EF)
        self.collection_metadata = config.get("collection_metadata", _DEFAULT_VSS)

        self.chroma_client = chromadb.PersistentClient(
            path=path, settings=Settings(anonymized_telemetry=False),
        )

        self.ddl_collection = self.chroma_client.get_or_create_collection(
            name="ddl",
            embedding_function=self.embedding_function,
            metadata=self.collection_metadata,
        )

        self.doc_collection = self.chroma_client.get_or_create_collection(
            name="doc",
            embedding_function=self.embedding_function,
            metadata=self.collection_metadata,
        )

        self.sql_collection = self.chroma_client.get_or_create_collection(
            name="sql",
            embedding_function=self.embedding_function,
            metadata=self.collection_metadata,
        )

    def generate_embedding(self, text: str, **kwargs) -> Sequence[float]:
        embedding = self.embedding_function([text])
        return embedding[0]

    def add_ddl(self, table_name: str, ddl: str, summary: str) -> str:
        content = json.dumps(
            {
                "summary": summary,
                "ddl": ddl,
            },
            ensure_ascii=False,
        )
        self.ddl_collection.add(
            documents=content,
            embeddings=self.generate_embedding(content),
            ids=table_name,
        )
        return table_name

    def get_all_ddl(self) -> pd.DataFrame:
        ddl_list = self.ddl_collection.get()

        ids = ddl_list["ids"]
        documents = ddl_list["documents"]

        contents = []
        for id, doc in zip(ids, documents):
            parsed = json.loads(doc)

            content = {
                "id": id,
                "document": parsed["summary"],
                "sql": parsed["ddl"]
            }
            contents.append(content)

        return pd.DataFrame(contents)

    def update_ddl(self, id: str, ddl: str, summary: str) -> str:
        content = json.dumps(
            {
                "summary": summary,
                "ddl": ddl,
            },
            ensure_ascii=False,
        )

        self.ddl_collection.update(
            ids=id,
            documents=content,
            embeddings=self.generate_embedding(content),
        )
        return id

    def add_doc(self, doc_name: str, documentation: str) -> str:
        self.doc_collection.add(
            documents=documentation,
            embeddings=self.generate_embedding(documentation),
            ids=doc_name,
        )
        return doc_name

    def get_all_doc(self) -> pd.DataFrame:
        doc_list = self.doc_collection.get()

        ids = doc_list["ids"]
        documents = doc_list["documents"]

        contents = []
        for id, doc in zip(ids, documents):
            content = {
                "id": id,
                "document": doc,
                "sql": None
            }
            contents.append(content)

        return pd.DataFrame(contents)

    def update_doc(self, id: str, doc: str) -> str:
        self.ddl_collection.update(
            ids=id,
            documents=doc,
            embeddings=self.generate_embedding(doc),
        )
        return id

    def add_sql(self, sql_alias: str, question: str, sql: str) -> str:
        content = json.dumps(
            {
                "question": question,
                "sql": sql,
            },
            ensure_ascii=False,
        )
        self.sql_collection.add(
            documents=content,
            embeddings=self.generate_embedding(content),
            ids=sql_alias,
        )
        return sql_alias

    def get_all_sql(self) -> pd.DataFrame:
        sql_list = self.sql_collection.get()

        ids = sql_list["ids"]
        documents = sql_list["documents"]

        contents = []
        for id, doc in zip(ids, documents):
            parsed = json.loads(doc)

            content = {
                "id": id,
                "document": parsed["question"],
                "sql": parsed["sql"]
            }
            contents.append(content)

        return pd.DataFrame(contents)

    def update_sql(self, id: str, question: str, sql: str) -> str:
        content = json.dumps(
            {
                "question": question,
                "sql": sql,
            },
            ensure_ascii=False,
        )

        self.sql_collection.update(
            ids=id,
            documents=content,
            embeddings=self.generate_embedding(content),
        )
        return id

    def delete_ddl(self, id: str) -> None:
        self.ddl_collection.delete(ids=[id])

    def delete_doc(self, id: str) -> None:
        self.doc_collection.delete(ids=[id])

    def delete_sql(self, id: str) -> None:
        self.sql_collection.delete(ids=[id])

    def get_all_data(self) -> pd.DataFrame:
        ddl_list = self.get_all_ddl()
        doc_list = self.get_all_doc()
        sql_list = self.get_all_sql()
        return pd.concat([ddl_list, doc_list, sql_list])

    def remove_training_data(self, id: str) -> None:
        if id.endswith("-ddl"):
            return self.ddl_collection.delete(ids=[id])
        elif id.endswith("-doc"):
            return self.doc_collection.delete(ids=[id])
        elif id.endswith("-sql"):
            return self.sql_collection.delete(ids=[id])
        else:
            raise ValueError("Id is invalid")

    def remove_collection(self, collection_name: str) -> bool:
        if collection_name in ("sql", "ddl", "doc"):
            try:
                self.chroma_client.delete_collection(name=collection_name)
            except ValueError:
                return False
            else:
                return True
        else:
            return False

    def _extract_documents(self, query_results: QueryResult) -> List[str]:
        if "documents" in query_results:
            return query_results["documents"][0]

        return list()

    def get_related_ddl(self, question: str, n_results: int = 5) -> list:
        documents = self._extract_documents(
            self.ddl_collection.query(
                query_texts=[question],
                n_results=n_results,
            )
        )

        return [json.loads(doc) for doc in documents]

    def get_related_doc(self, question: str, n_results: int = 5) -> list:
        return self._extract_documents(
            self.doc_collection.query(
                query_texts=[question],
                n_results=n_results,
            )
        )

    def get_related_sql(self, question: str, n_results: int = 5) -> list:
        documents = self._extract_documents(
            self.sql_collection.query(
                query_texts=[question],
                n_results=n_results,
            )
        )

        return [json.loads(doc) for doc in documents]

