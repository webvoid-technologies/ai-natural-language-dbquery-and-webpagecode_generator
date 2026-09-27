"""Generate SQLite SELECT queries from natural language using Groq."""

from __future__ import annotations

import logging

from app.services import groq_service, prompts, schema_service
from app.utils import validators

logger = logging.getLogger(__name__)


class SQLGenerationError(RuntimeError):
    """Raised when SQL generation fails."""


async def generate_sql(user_query: str, schema_text: str | None = None) -> str:
    """Generate raw SQL from a natural-language question."""
    if schema_text is None:
        schema_text = schema_service.get_formatted_schema()

    prompt = prompts.build_sql_generation_prompt(schema_text, user_query)
    try:
        content = await groq_service.get_service().generate_text(
            system_prompt=prompts.SQL_GENERATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.2,
            max_tokens=2048,
        )
    except groq_service.GroqServiceError as exc:
        logger.exception("SQL generation failed")
        raise SQLGenerationError(f"Could not generate SQL: {exc}") from exc

    sql = validators.normalize_sql(content)
    if not sql.lower().startswith(("select", "with")):
        raise SQLGenerationError("Generated response is not a valid SELECT query.")
    return sql
