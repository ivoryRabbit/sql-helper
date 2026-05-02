from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    @abstractmethod
    async def test_connection(self, config: dict) -> None:
        """Attempt a connection and raise on failure."""
        ...

    @abstractmethod
    async def execute_query(
        self, config: dict, sql: str, limit: int = 5000
    ) -> tuple[list[dict], list[dict]]:
        """Execute a read-only SQL query.

        Returns:
            (rows, columns) where rows is a list of dicts and columns is a list of
            {"name": str, "type": str} dicts describing the result set schema.

        Raises:
            ValueError: if the statement is not a SELECT.
            Exception: on connection or execution failure.
        """
        ...
