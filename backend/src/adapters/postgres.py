import psycopg

from adapters.base import BaseAdapter

_NUMERIC_OID = frozenset({
    20, 21, 23, 700, 701, 1700,   # int2/4/8, float4/8, numeric
})
_DATE_OID = frozenset({1082, 1083, 1114, 1184, 1266})  # date, time, timestamp[tz], timetz


def _pg_type_name(oid: int) -> str:
    _MAP = {
        16: "boolean",
        20: "bigint", 21: "smallint", 23: "integer",
        700: "real", 701: "double precision",
        1700: "numeric",
        25: "text", 1043: "varchar", 1042: "char",
        1082: "date", 1083: "time", 1114: "timestamp", 1184: "timestamptz",
        114: "json", 3802: "jsonb",
        2950: "uuid",
    }
    return _MAP.get(oid, f"oid:{oid}")


def _build_conn_kwargs(config: dict) -> dict:
    return dict(
        host=config.get("host", "localhost"),
        port=int(config.get("port", 5432)),
        dbname=config.get("database", ""),
        user=config.get("username", ""),
        password=config.get("password", ""),
        connect_timeout=int(config.get("connection_timeout", 5)),
    )


class PostgresAdapter(BaseAdapter):
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
            # Wrap in a limit subquery so we never return enormous result sets
            limited_sql = f"SELECT * FROM ({sql}) AS _q LIMIT {int(limit)}"
            async with conn.cursor() as cur:
                await cur.execute(limited_sql)
                raw_rows = await cur.fetchall()
                desc = cur.description or []

            columns = [
                {"name": col.name, "type": _pg_type_name(col.type_code)}
                for col in desc
            ]
            col_names = [c["name"] for c in columns]
            rows = [dict(zip(col_names, row)) for row in raw_rows]
            return rows, columns
        finally:
            await conn.close()
