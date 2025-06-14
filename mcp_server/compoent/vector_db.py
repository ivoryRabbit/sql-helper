from typing import Optional, List, Sequence

import chromadb
from chromadb import QueryResult
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from models.dto.table_document import TableDocument
from utils.uuid import generate_id


class VectorDB:
    def __init__(self, path: Optional[str] = None):
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        self.collection_metadata = _DEFAULT_VSS = {"hnsw:space": "cosine"}

        self.client = chromadb.PersistentClient(
            path=path, settings=Settings(anonymized_telemetry=False),
        )

        self.table_documents = self.client.get_or_create_collection(
            name="table_documents",
            embedding_function=self.embedding_function,
            metadata=self.collection_metadata,
        )

    def generate_embedding(self, text: str) -> Sequence[float]:
        embedding = self.embedding_function([text])
        return embedding[0]

    def generate_embedding_bulk(self, texts: List[str]) -> List[Sequence[float]]:
        embedding = self.embedding_function(texts)
        return embedding

    def add_table_document(self, table_document: TableDocument) -> str:
        entity_id = generate_id(table_document.table_name)
        document = table_document.document
        metadata = {"table_name": table_document.table_name}

        self.table_documents.upsert(
            ids=entity_id,
            documents=document,
            metadatas=metadata,
            embeddings=self.generate_embedding(document),
        )

        return entity_id

    def add_table_documents(self, table_documents: List[TableDocument]) -> List[str]:
        entity_ids = []
        documents = []
        metadatas = []

        for table_document in table_documents:
            entity_id = generate_id(table_document.table_name)
            document = table_document.document
            metadata = {"table_name": table_document.table_name}

            entity_ids.append(entity_id)
            documents.append(document)
            metadatas.append(metadata)

        self.table_documents.upsert(
            ids=entity_ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=self.generate_embedding_bulk(documents),
        )

        return entity_ids

    def get_table_document(self, table_name: str) -> TableDocument:
        query_result = self.table_documents.get(
            where={"table_name": table_name}
        )

        table_document = TableDocument(
            table_name=query_result["metadatas"][0]["table_name"],
            document=query_result["documents"][0]
        )

        return table_document

    def get_table_documents(self, limit: int = 10, offset: int = 0) -> List[TableDocument]:
        query_result = self.table_documents.get(limit=limit, offset=offset)

        documents = query_result["documents"]
        metadatas = query_result["metadatas"]

        table_documents = []
        for document, metadata in zip(documents, metadatas):
            table_document = TableDocument(
                table_name=metadata["table_name"],
                document=document,
            )

            table_documents.append(table_document)

        return table_documents

    def modify_table_document(self, table_name: str, document: str) -> str:
        table_document = TableDocument(table_name=table_name, document=document)
        return self.add_table_document(table_document)

    def remove_table_document(self, table_name: str) -> str:
        entity_id = generate_id(table_name)
        self.table_documents.delete(ids=[entity_id])
        return entity_id

    def remove_all_documents(self) -> None:
        self.table_documents.delete()

    def remove_collection(self) -> None:
        self.client.delete_collection("table_documents")

    def get_relevant_tables(self, question: str, n_results: int = 5) -> List[TableDocument]:
        query_result: QueryResult = self.table_documents.query(
            query_texts=[question],
            n_results=n_results,
            include=["documents", "metadatas"],
        )

        documents = query_result["documents"][0]
        metadatas = query_result["metadatas"][0]

        table_documents = []
        for document, metadata in zip(documents, metadatas):
            table_document = TableDocument(
                table_name=metadata["table_name"],
                document=document
            )

            table_documents.append(table_document)

        return table_documents
