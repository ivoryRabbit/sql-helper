import json
from typing import List, Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text, Engine

from clients import rag, trino
from compoent.vector_db import VectorDB
from models.response.table_info import TableInfo


router = APIRouter(prefix="/api/v1", tags=["MCP"])


@router.get(
    path="/relevant-tables",
    response_model=List[TableInfo],
)
async def get_relevant_tables(
    question: str,
    n_results: int,
    rag_client: Annotated[VectorDB, Depends(rag.get_client)],
) -> List[TableInfo]:
    table_documents = rag_client.get_relevant_tables(question, n_results=n_results)

    table_infos = []
    for table_document in table_documents:
        table_info = TableInfo.from_document(table_document)
        table_infos.append(table_info)

    return table_infos


@router.get(
    path="/query-results",
    response_model=str,
)
async def get_query_results(
    sql_text: str,
    engine: Annotated[Engine, Depends(trino.get_client)],
) -> str:
    statement = text(sql_text)

    with engine.connect() as conn:
        rows = conn.execute(statement).mappings().fetchall()

    return json.dumps([dict(row) for row in rows])
