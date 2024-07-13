import hashlib
import json
import uuid
from typing import Union, Sequence

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

        n_results = config.get("n_results", 10)

        self.n_results_sql = config.get("n_results_sql", n_results)
        self.n_results_doc = config.get("n_results_doc", n_results)
        self.n_results_ddl = config.get("n_results_ddl", n_results)

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

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
            },
            ensure_ascii=False,
        )
        id = self._generate_uuid(question_sql_json) + "-sql"
        self.sql_collection.add(
            documents=question_sql_json,
            embeddings=self.generate_embedding(question_sql_json),
            ids=id,
        )
        return id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        id = self._generate_uuid(ddl) + "-ddl"
        self.ddl_collection.add(
            documents=ddl,
            embeddings=self.generate_embedding(ddl),
            ids=id,
        )
        return id

    def add_doc(self, documentation: str, **kwargs) -> str:
        id = self._generate_uuid(documentation) + "-doc"
        self.doc_collection.add(
            documents=documentation,
            embeddings=self.generate_embedding(documentation),
            ids=id,
        )
        return id

    def get_training_data(self, id: str, **kwargs) -> pd.DataFrame:
        if id.endswith("-ddl"):
            data = self.ddl_collection.get(ids=[id])
        elif id.endswith("-doc"):
            data = self.doc_collection.get(ids=[id])
        elif id.endswith("-sql"):
            data = self.sql_collection.get(ids=[id])
        else:
            raise ValueError("Id is invalid")

        rows = []
        for id, doc in zip(data["ids"], data["documents"]):
            row = {
                "id": id,
                "question": None,
                "content": doc
            }
            rows.append(row)

        df = pd.DataFrame(rows)

        return df

    def remove_training_data(self, id: str, **kwargs) -> None:
        if id.endswith("-ddl"):
            return self.ddl_collection.delete(ids=[id])
        elif id.endswith("-doc"):
            return self.doc_collection.delete(ids=[id])
        elif id.endswith("-sql"):
            return self.sql_collection.delete(ids=[id])
        else:
            raise ValueError("Id is invalid")

    def get_all_data(self, **kwargs) -> pd.DataFrame:
        sql_data = self.sql_collection.get()

        df = pd.DataFrame()

        if sql_data is not None:
            # Extract the documents and ids
            documents = [json.loads(doc) for doc in sql_data["documents"]]
            ids = sql_data["ids"]

            # Create a DataFrame
            df_sql = pd.DataFrame(
                {
                    "id": ids,
                    "question": [doc["question"] for doc in documents],
                    "content": [doc["sql"] for doc in documents],
                }
            )

            df_sql["training_data_type"] = "sql"

            df = pd.concat([df, df_sql])

        ddl_data = self.ddl_collection.get()

        if ddl_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in ddl_data["documents"]]
            ids = ddl_data["ids"]

            # Create a DataFrame
            df_ddl = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                }
            )

            df_ddl["training_data_type"] = "ddl"

            df = pd.concat([df, df_ddl])

        doc_data = self.doc_collection.get()

        if doc_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in doc_data["documents"]]
            ids = doc_data["ids"]

            # Create a DataFrame
            df_doc = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                }
            )

            df_doc["training_data_type"] = "documentation"

            df = pd.concat([df, df_doc])

        return df

    def remove_collection(self, collection_name: str) -> bool:
        if collection_name in ("sql", "ddl", "documentation"):
            try:
                self.chroma_client.delete_collection(name=collection_name)
            except ValueError:
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def _extract_documents(query_results: Union[pd.DataFrame, QueryResult]) -> list:
        if query_results is None:
            return []

        if "documents" in query_results:
            documents = query_results["documents"]

            if len(documents) == 1 and isinstance(documents[0], list):
                try:
                    documents = [json.loads(doc) for doc in documents[0]]
                except Exception as e:
                    return documents[0]

            return documents

    def get_related_ddl(self, question: str, **kwargs) -> list:
        return ChromaDBVectorStore._extract_documents(
            self.ddl_collection.query(
                query_texts=[question],
                n_results=self.n_results_ddl,
            )
        )

    def get_related_doc(self, question: str, **kwargs) -> list:
        return ChromaDBVectorStore._extract_documents(
            self.doc_collection.query(
                query_texts=[question],
                n_results=self.n_results_doc,
            )
        )

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        return ChromaDBVectorStore._extract_documents(
            self.sql_collection.query(
                query_texts=[question],
                n_results=self.n_results_sql,
            )
        )

    def _generate_uuid(self, content: Union[str, bytes]) -> str:
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
