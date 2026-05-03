from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.catalog import (
        CatalogSyncActivityInput,
        generate_catalog_embeddings,
        introspect_postgres,
        upsert_catalog_data,
    )


@dataclass
class CatalogSyncInput:
    data_source_id: str
    config: dict


@dataclass
class CatalogSyncResult:
    data_source_id: str
    schemas_synced: int
    tables_synced: int
    columns_synced: int
    documents_indexed: int


@workflow.defn
class CatalogSyncWorkflow:
    @workflow.run
    async def run(self, input: CatalogSyncInput) -> CatalogSyncResult:
        metadata = await workflow.execute_activity(
            introspect_postgres,
            input.config,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        upsert_input = CatalogSyncActivityInput(
            data_source_id=input.data_source_id,
            metadata=metadata,
        )
        upsert_result = await workflow.execute_activity(
            upsert_catalog_data,
            upsert_input,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        documents_indexed = await workflow.execute_activity(
            generate_catalog_embeddings,
            input.data_source_id,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )

        return CatalogSyncResult(
            data_source_id=input.data_source_id,
            schemas_synced=upsert_result["schemas_synced"],
            tables_synced=upsert_result["tables_synced"],
            columns_synced=upsert_result["columns_synced"],
            documents_indexed=documents_indexed,
        )
