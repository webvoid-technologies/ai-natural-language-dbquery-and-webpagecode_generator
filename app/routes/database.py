"""Natural Language to SQL routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services import history_service, schema_service, sql_orchestrator
from app.utils.formatter import rows_to_csv, rows_to_html_table

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class ExecuteRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    sql: str = Field(min_length=1)


def _history_record(payload: dict[str, Any], status: str, error: str | None = None) -> dict[str, Any]:
    record = {
        "user_query": payload.get("user_query"),
        "generated_sql": payload.get("sql"),
        "valid": payload.get("valid", False),
        "validation_reason": payload.get("reason"),
        "retry_count": payload.get("retry_count", 0),
        "execution_time": payload.get("execution_time"),
        "row_count": payload.get("row_count", 0),
        "status": status,
        "error": error,
    }
    return history_service.history_store.add(record)


@router.post("/database/query")
async def generate_query(payload: QueryRequest) -> dict[str, Any]:
    """Generate SQL only (no execution) for a natural-language question."""
    try:
        schema_text = schema_service.get_formatted_schema()
        from app.services import sql_generator
        sql = await sql_generator.generate_sql(payload.question, schema_text)
        return {"sql": sql, "question": payload.question}
    except sql_generator.SQLGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/database/execute")
async def execute_query(payload: QueryRequest) -> dict[str, Any]:
    """Full pipeline: generate, validate with retries, execute, and store history."""
    try:
        result = await sql_orchestrator.process_query(payload.question)
        html_table = rows_to_html_table(result["rows"])
        response = {
            "sql": result["sql"],
            "valid": result["valid"],
            "reason": result["reason"],
            "retry_count": result["retry_count"],
            "execution_time": result["execution_time"],
            "row_count": result["row_count"],
            "html_table": html_table,
            "csv": rows_to_csv(result["rows"]),
        }
        _history_record(result, "success")
        return response
    except sql_orchestrator.SQLOrchestratorError as exc:
        _history_record({"user_query": payload.question, "sql": "", "reason": str(exc)}, "error", str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during query execution")
        _history_record({"user_query": payload.question, "sql": "", "reason": str(exc)}, "error", str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Query processing failed: {exc}",
        ) from exc


@router.post("/database/execute-direct")
async def execute_direct(payload: ExecuteRequest) -> dict[str, Any]:
    """Execute a pre-validated SQL query directly (used for corrected SQL)."""
    from app.utils import validators
    from app.services import sql_executor

    if not validators.is_safe_sql(payload.sql):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only safe SELECT queries are allowed.",
        )
    try:
        execution = await sql_executor.execute_query(payload.sql)
        html_table = rows_to_html_table(execution["rows"])
        response = {
            "sql": payload.sql,
            "valid": True,
            "reason": "Manually corrected SQL executed.",
            "retry_count": 0,
            "execution_time": execution["execution_time"],
            "row_count": execution["row_count"],
            "html_table": html_table,
            "csv": rows_to_csv(execution["rows"]),
        }
        _history_record(
            {
                "user_query": payload.question,
                "sql": payload.sql,
                "valid": True,
                "reason": "Direct execution",
                "retry_count": 0,
                **execution,
            },
            "success",
        )
        return response
    except sql_executor.SQLExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/database/schema/refresh")
async def refresh_schema() -> dict[str, Any]:
    """Invalidate the schema cache and re-read from the database."""
    schema_service.clear_schema_cache()
    schema = schema_service.read_schema(force_refresh=True)
    return {"tables": list(schema["tables"].keys()), "table_count": len(schema["tables"])}
