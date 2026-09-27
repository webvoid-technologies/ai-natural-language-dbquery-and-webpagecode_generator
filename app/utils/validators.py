"""Input and SQL safety validators."""

from __future__ import annotations

import re

UNSAFE_KEYWORDS = {
    "drop",
    "delete",
    "update",
    "insert",
    "alter",
    "create",
    "truncate",
    "exec",
    "execute",
    "call",
    "grant",
    "revoke",
    "commit",
    "rollback",
    "vacuum",
    "analyze",
}


def is_safe_sql(sql: str) -> bool:
    """Reject any SQL that contains non-SELECT/WITH statements or unsafe keywords."""
    if not sql or not isinstance(sql, str):
        return False

    # Strip comments and strings crudely for keyword scanning.
    cleaned = re.sub(r"--[^\n]*", " ", sql)
    cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"'[^']*'", " '' ", cleaned)
    cleaned = re.sub(r'"[^"]*"', ' "" ', cleaned)
    tokens = re.findall(r"[a-zA-Z_]+", cleaned.lower())

    for token in tokens:
        if token in UNSAFE_KEYWORDS:
            return False

    return True


def normalize_sql(sql: str) -> str:
    """Remove markdown fences and trim the SQL string."""
    sql = sql.strip()
    if sql.startswith("```"):
        sql = sql.strip("`")
        for lang in ("sql", "sqlite", "postgresql", "postgres"):
            if sql.lower().startswith(lang):
                sql = sql[len(lang):].lstrip()
                break
    return sql.strip()
