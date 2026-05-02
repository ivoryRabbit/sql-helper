import httpx

from adapters.base import BaseAdapter


class TrinoAdapter(BaseAdapter):
    async def test_connection(self, config: dict) -> None:
        url = config.get("coordinator_url", "").rstrip("/")
        if not url:
            raise ValueError("coordinator_url is required for Trino connections")

        auth = None
        username = config.get("username")
        password = config.get("password")
        if username:
            auth = (username, password or "")

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{url}/v1/info",
                auth=auth,
                headers={"X-Trino-Catalog": config.get("catalog", "")},
            )
            resp.raise_for_status()

    async def execute_query(
        self, config: dict, sql: str, limit: int = 5000
    ) -> tuple[list[dict], list[dict]]:
        """Execute a query via Trino REST API (Statement API v1)."""
        stripped = sql.strip().upper()
        if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
            raise ValueError("Only SELECT statements are allowed")

        url = config.get("coordinator_url", "").rstrip("/")
        if not url:
            raise ValueError("coordinator_url is required for Trino connections")

        username = config.get("username", "trino")
        password = config.get("password")
        auth = (username, password or "") if password else None

        limited_sql = f"SELECT * FROM ({sql}) AS _q LIMIT {int(limit)}"
        headers = {
            "X-Trino-User": username,
            "X-Trino-Catalog": config.get("catalog", ""),
            "X-Trino-Schema": config.get("schema", ""),
        }

        rows: list[dict] = []
        columns: list[dict] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{url}/v1/statement",
                content=limited_sql,
                headers=headers,
                auth=auth,
            )
            resp.raise_for_status()
            data = resp.json()

            # Follow next-URI pagination until done
            while True:
                if "columns" in data and not columns:
                    columns = [
                        {"name": col["name"], "type": col["type"]}
                        for col in data["columns"]
                    ]

                for row in data.get("data", []):
                    rows.append(dict(zip([c["name"] for c in columns], row)))

                next_uri = data.get("nextUri")
                if not next_uri:
                    break

                resp = await client.get(next_uri, headers=headers, auth=auth)
                resp.raise_for_status()
                data = resp.json()

        return rows, columns
