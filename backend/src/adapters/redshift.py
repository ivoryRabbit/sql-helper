import psycopg

from adapters.base import BaseAdapter


def _build_conn_kwargs(config: dict) -> dict:
    host = config.get("host") or (
        f"{config['cluster_id']}.{config['region']}.redshift.amazonaws.com"
        if config.get("cluster_id") and config.get("region")
        else "localhost"
    )
    return dict(
        host=host,
        port=int(config.get("port", 5439)),
        dbname=config.get("database", ""),
        user=config.get("username", ""),
        password=config.get("password", ""),
        connect_timeout=int(config.get("connection_timeout", 5)),
        sslmode=config.get("ssl_mode", "require"),
    )


class RedshiftAdapter(BaseAdapter):
    """Redshift is wire-compatible with PostgreSQL; uses psycopg v3 async."""

    async def test_connection(self, config: dict) -> None:
        conn = await psycopg.AsyncConnection.connect(**_build_conn_kwargs(config))
        await conn.close()

    async def execute_query(
        self, config: dict, sql: str, limit: int = 5000
    ) -> tuple[list[dict], list[dict]]:
        stripped = sql.strip().upper()
        if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
            raise ValueError("Only SELECT statements are allowed")

        conn = await psycopg.AsyncConnection.connect(**_build_conn_kwargs(config))
        try:
            limited_sql = f"SELECT * FROM ({sql}) AS _q LIMIT {int(limit)}"
            async with conn.cursor() as cur:
                await cur.execute(limited_sql)
                raw_rows = await cur.fetchall()
                desc = cur.description or []

            columns = [{"name": col.name, "type": str(col.type_code)} for col in desc]
            col_names = [c["name"] for c in columns]
            rows = [dict(zip(col_names, row)) for row in raw_rows]
            return rows, columns
        finally:
            await conn.close()
