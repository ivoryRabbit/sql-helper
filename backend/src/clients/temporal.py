import logging

from temporalio.client import Client, WorkflowHandle

logger = logging.getLogger(__name__)


class TemporalClient:
    DEFAULT_NAMESPACE = "default"

    def __init__(self, address: str, namespace: str = DEFAULT_NAMESPACE) -> None:
        self._address = address
        self._namespace = namespace
        self._client: Client | None = None

    async def connect(self) -> None:
        try:
            self._client = await Client.connect(self._address, namespace=self._namespace)
            logger.info("Temporal connected: %s (namespace=%s)", self._address, self._namespace)
        except Exception as exc:
            logger.warning("Temporal unavailable (%s) — workflow dispatch disabled", exc)
            self._client = None

    async def close(self) -> None:
        self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    async def start_workflow(self, workflow, *args, id: str, task_queue: str, **kwargs) -> WorkflowHandle:
        if self._client is None:
            raise RuntimeError("Temporal client is not connected")
        return await self._client.start_workflow(workflow, *args, id=id, task_queue=task_queue, **kwargs)

    def get_workflow_handle(self, workflow_id: str) -> WorkflowHandle:
        if self._client is None:
            raise RuntimeError("Temporal client is not connected")
        return self._client.get_workflow_handle(workflow_id)
