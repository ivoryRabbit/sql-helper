from typing import List, Annotated

from fastapi import APIRouter, Depends

from clients import rag
from compoent.vector_db import VectorDB
from models.response.table_info import TableInfo

router = APIRouter(prefix="/api/v1", tags=["RAG"])


@router.get(
    path="/documents/{table_name}",
    response_model=TableInfo,
)
async def get_relevant_tables(
    table_name: str,
    rag_client: Annotated[VectorDB, Depends(rag.get_client)],
) -> TableInfo:
    table_document = rag_client.get_table_document(table_name)
    return TableInfo.from_document(table_document)
