from datetime import timedelta
from typing import Optional

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from component.activities import TextToSQLParams, submit_prompts


@workflow.defn
class TextToSQLWorkflow:
    @workflow.run
    async def run(self, dialect: str, question: str) -> Optional[str]:
        return await workflow.execute_activity(
            submit_prompts,
            TextToSQLParams(dialect=dialect, question=question),
            start_to_close_timeout=timedelta(seconds=30),
        )
