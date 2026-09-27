"""Execute validated SELECT queries on the local SQLite database."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app import config

logger = logging.getLogger(__name__)


class SQLExecutionError(RuntimeError):
    """Raised when SQL execution fails."""


def _get_engine():
    if not config.DATABASE_URL:
        raise SQLExecutionError("DATABASE_URL is not configured.")
    return create_engine(config.DATABASE_URL, pool_pre_ping=True, future=True)


def _sqlite_compat(sql: str) -> str:
    """Translate common PostgreSQL idioms the LLM may still emit into SQLite."""
    # SQLite LIKE is already case-insensitive for ASCII.
    sql = re.sub(r"\bILIKE\b", "LIKE", sql, flags=re.IGNORECASE)
    # Plain single-column casts (::int, ::text) → CAST isn't needed; strip to the column.
    sql = re.sub(r"::(?:integer|int|bigint|text|varchar|numeric|real|date)\b", "", sql, flags=re.IGNORECASE)
    return sql


async def execute_query(sql: str) -> dict[str, Any]:
    """Execute a read-only query and return results with timing metadata."""
    engine = _get_engine()
    sql = _sqlite_compat(sql)
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(row) for row in result.mappings()]
            elapsed = round(time.perf_counter() - start, 4)
            return {
                "rows": rows,
                "row_count": len(rows),
                "execution_time": elapsed,
            }
    except SQLAlchemyError as exc:
        logger.exception("SQL execution failed: %s", sql)
        raise SQLExecutionError(f"Database error: {exc}") from exc
