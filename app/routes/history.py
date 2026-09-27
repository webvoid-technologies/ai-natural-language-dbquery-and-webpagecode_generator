"""Query history API routes."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query

from app.services import history_service

router = APIRouter()


@router.get("/api/history")
async def list_history(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
) -> dict[str, Any]:
    records = history_service.history_store.list(search=search, status=status)
    return {"records": records, "total": len(records)}


@router.delete("/api/history")
async def clear_history() -> dict[str, str]:
    history_service.history_store.clear()
    return {"message": "History cleared."}
