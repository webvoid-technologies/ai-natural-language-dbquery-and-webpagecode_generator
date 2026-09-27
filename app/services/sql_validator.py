"""Validate generated SQL against schema and safety using Groq."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services import groq_service, prompts, schema_service
from app.utils import validators

logger = logging.getLogger(__name__)


class SQLValidationError(RuntimeError):
    """Raised when validation cannot be completed."""


async def validate_sql(user_query: str, generated_sql: str, schema_text: str | None = None) -> dict[str, Any]:
    """Validate SQL and return a standardized result dictionary."""
    if schema_text is None:
        schema_text = schema_service.get_formatted_schema()

    if not validators.is_safe_sql(generated_sql):
        return {
            "valid": False,
            "reason": "Safety check failed: only SELECT/WITH queries are allowed.",
            "corrected_sql": None,
        }

    prompt = prompts.build_sql_validation_prompt(schema_text, user_query, generated_sql)
    try:
        content = await groq_service.get_service().generate_text(
            system_prompt=prompts.SQL_VALIDATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.1,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
    except groq_service.GroqServiceError as exc:
        logger.exception("SQL validation failed")
        raise SQLValidationError(f"Could not validate SQL: {exc}") from exc

    try:
        cleaned = validators.normalize_sql(content)
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise SQLValidationError("Validator returned invalid JSON.") from exc

    result.setdefault("valid", False)
    result.setdefault("reason", "")
    result.setdefault("corrected_sql", None)
    return result
