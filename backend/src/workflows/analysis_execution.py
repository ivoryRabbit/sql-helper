from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities.analysis import (
        AnalysisExecutionInput,
        execute_and_store_query,
        compute_and_store_stats,
        generate_and_store_insights,
    )


@dataclass
class AnalysisWorkflowInput:
    execution_id: str
    data_source_id: str
    sql: str
    limit_rows: int = 1000


@dataclass
class AnalysisWorkflowResult:
    execution_id: str
    status: str
    row_count: int
    execution_time_ms: int


@workflow.defn
class AnalysisExecutionWorkflow:
    @workflow.run
    async def run(self, input: AnalysisWorkflowInput) -> AnalysisWorkflowResult:
        activity_input = AnalysisExecutionInput(
            execution_id=input.execution_id,
            data_source_id=input.data_source_id,
            sql=input.sql,
            limit_rows=input.limit_rows,
        )

        exec_result = await workflow.execute_activity(
            execute_and_store_query,
            activity_input,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=workflow.RetryPolicy(maximum_attempts=1),
        )

        await workflow.execute_activity(
            compute_and_store_stats,
            input.execution_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=workflow.RetryPolicy(maximum_attempts=2),
        )

        await workflow.execute_activity(
            generate_and_store_insights,
            input.execution_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=workflow.RetryPolicy(maximum_attempts=2),
        )

        return AnalysisWorkflowResult(
            execution_id=input.execution_id,
            status="completed",
            row_count=exec_result["row_count"],
            execution_time_ms=exec_result["execution_time_ms"],
        )
