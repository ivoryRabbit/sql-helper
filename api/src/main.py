import logging
from contextlib import asynccontextmanager
from uuid import uuid4

import sqlparse
import uvicorn
from fastapi import FastAPI, HTTPException

from client import temporal
from component.workflow import TextToSQLWorkflow
from model.request.question import Question
from model.response.sql_query import SQLQuery

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await temporal.init_client()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/text-to-sql")
async def translate(question: Question) -> SQLQuery:
    client = temporal.get_client()
    try:
        raw_sql = await client.execute_workflow(
            TextToSQLWorkflow.run,
            args=[question.dialect, question.question],
            id=f"question-{uuid4()}",
            task_queue="text-to-sql-task-queue",
        )

        sql = sqlparse.format(raw_sql, indent_tabs=True, keyword_case="upper")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return SQLQuery(sql=sql)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
