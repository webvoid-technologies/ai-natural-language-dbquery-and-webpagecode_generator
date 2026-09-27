"""Orchestrate generation, validation, retry and execution of natural-language SQL."""

from __future__ import annotations

import logging
from typing import Any

from app import config
from app.services import schema_service, sql_executor, sql_generator, sql_validator
from app.utils import validators

logger = logging.getLogger(__name__)


class SQLOrchestratorError(RuntimeError):
    """Raised when the SQL pipeline cannot produce a valid query."""


async def process_query(user_query: str) -> dict[str, Any]:
    """Generate, validate (with retries), execute and return a full result."""
    schema_text = schema_service.get_formatted_schema()

    current_sql = ""
    validation: dict[str, Any] = {"valid": False, "reason": "", "corrected_sql": None}
    retries = 0
    max_retries = config.SQL_MAX_RETRIES

    # Build validation feedback into a running correction prompt.
    for attempt in range(max_retries + 1):
        try:
            if attempt == 0 or not current_sql:
                current_sql = await sql_generator.generate_sql(user_query, schema_text)
            else:
                feedback = f"Previous SQL: {current_sql}\nValidator feedback: {validation.get('reason', '')}\nPlease generate a corrected SELECT query."
                current_sql = await sql_generator.generate_sql(
                    user_query + "\n\n" + feedback, schema_text
                )
        except sql_generator.SQLGenerationError as exc:
            raise SQLOrchestratorError(str(exc)) from exc

        # Final safety gate before execution.
        if not validators.is_safe_sql(current_sql):
            validation = {
                "valid": False,
                "reason": "Safety check failed: only SELECT/WITH queries are allowed.",
                "corrected_sql": None,
            }
            retries += 1
            if retries > max_retries:
                raise SQLOrchestratorError(
                    "Could not generate a safe SELECT query after maximum retries."
                )
            continue

        validation = await sql_validator.validate_sql(user_query, current_sql, schema_text)

        if validation.get("valid"):
            break

        retries += 1
        if retries <= max_retries and validation.get("corrected_sql"):
            current_sql = validators.normalize_sql(validation["corrected_sql"])
    else:
        # Loop exhausted without a valid query.
        raise SQLOrchestratorError(
            f"SQL validation failed after {retries} retries. Reason: {validation.get('reason')}"
        )

    execution = await sql_executor.execute_query(current_sql)

    return {
        "user_query": user_query,
        "sql": current_sql,
        "valid": True,
        "reason": validation.get("reason", "Query matches schema and user request."),
        "retry_count": retries,
        "execution_time": execution["execution_time"],
        "row_count": execution["row_count"],
        "rows": execution["rows"],
    }
