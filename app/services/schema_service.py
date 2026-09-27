"""Read and cache the live SQLite schema for SQL generation prompts."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import create_engine, text

from app import config

logger = logging.getLogger(__name__)

_schema_cache: dict[str, Any] | None = None


def _get_engine():
    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")
    return create_engine(config.DATABASE_URL, pool_pre_ping=True, future=True)


def _fetch_columns(conn, table_name: str) -> list[dict[str, Any]]:
    result = conn.execute(text(f'PRAGMA table_info("{table_name}")'))
    # PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
    return [
        {
            "name": row.name,
            "type": row.type or "TEXT",
            "nullable": not bool(row.notnull),
            "default": row.dflt_value,
            "pk": bool(row.pk),
        }
        for row in result.mappings()
    ]


def _fetch_pks(conn, table_name: str) -> list[str]:
    result = conn.execute(text(f'PRAGMA table_info("{table_name}")'))
    return [row.name for row in result.mappings() if row.pk]


def _fetch_fks(conn, table_name: str) -> list[dict[str, Any]]:
    result = conn.execute(text(f'PRAGMA foreign_key_list("{table_name}")'))
    # PRAGMA foreign_key_list columns include: table, from, to
    return [
        {
            "column": row["from"],
            "references_table": row.table,
            "references_column": row.to,
        }
        for row in result.mappings()
    ]


def _format_schema(schema: dict[str, Any]) -> str:
    lines = []
    for table_name, table in schema["tables"].items():
        lines.append(f"TABLE: {table_name}")
        for col in table["columns"]:
            marker = " PK" if col["name"] in table["primary_keys"] else ""
            fk = next((f" -> {fk['references_table']}.{fk['references_column']}" for fk in table["foreign_keys"] if fk["column"] == col["name"]), "")
            lines.append(f"  - {col['name']}: {col['type']}{marker}{fk}")
        lines.append("")
    return "\n".join(lines)


def read_schema(force_refresh: bool = False) -> dict[str, Any]:
    """Fetch the live database schema and cache it in memory."""
    global _schema_cache
    if _schema_cache is not None and not force_refresh:
        return _schema_cache

    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """))
        table_names = [row.name for row in result.mappings()]

        tables: dict[str, Any] = {}
        for name in table_names:
            row_count = conn.execute(text(f'SELECT COUNT(*) AS c FROM "{name}"')).scalar()
            tables[name] = {
                "columns": _fetch_columns(conn, name),
                "primary_keys": _fetch_pks(conn, name),
                "foreign_keys": _fetch_fks(conn, name),
                "row_count": row_count,
            }

        schema = {
            "database": "sqlite",
            "tables": tables,
            "formatted": _format_schema({"tables": tables}),
            "generated_at": None,
        }

    _schema_cache = schema
    logger.info("Schema cached with %d tables", len(tables))
    return schema


def get_formatted_schema() -> str:
    """Return a compact text representation of the schema for prompts."""
    return read_schema()["formatted"]


def clear_schema_cache() -> None:
    """Invalidate the in-memory schema cache."""
    global _schema_cache
    _schema_cache = None
