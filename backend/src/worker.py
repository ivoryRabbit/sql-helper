import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.worker import Worker

from activities.catalog import (
    generate_catalog_embeddings,
    introspect_postgres,
    upsert_catalog_data,
)
from activities.analysis import (
    compute_and_store_stats,
    execute_and_store_query,
    generate_and_store_insights,
)
from workflows.catalog_sync import CatalogSyncWorkflow
from workflows.analysis_execution import AnalysisExecutionWorkflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

TASK_QUEUE = "sql-helper"


async def main() -> None:
    address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    logger.info("Connecting to Temporal at %s", address)
    client = await Client.connect(address)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[CatalogSyncWorkflow, AnalysisExecutionWorkflow],
        activities=[
            introspect_postgres,
            upsert_catalog_data,
            generate_catalog_embeddings,
            execute_and_store_query,
            compute_and_store_stats,
            generate_and_store_insights,
        ],
    )

    logger.info("Worker started — task_queue=%s", TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
