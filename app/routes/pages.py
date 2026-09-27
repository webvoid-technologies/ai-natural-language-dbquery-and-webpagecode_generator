"""Jinja-rendered page routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import config
from app.services import history_service, prompts, schema_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": config.APP_NAME,
            "config_status": config.is_configured(),
        },
    )


@router.get("/database", response_class=HTMLResponse)
async def database_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="database.html",
        context={"examples": prompts.EXAMPLE_QUERIES},
    )


@router.get("/webpage", response_class=HTMLResponse)
async def webpage_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="webpage.html")


@router.get("/schema", response_class=HTMLResponse)
async def schema_page(request: Request) -> HTMLResponse:
    schema = {"tables": {}}
    schema_error = None
    try:
        schema = schema_service.read_schema()
    except Exception as exc:
        schema_error = str(exc)
    return templates.TemplateResponse(
        request=request,
        name="schema.html",
        context={"schema": schema, "schema_error": schema_error},
    )


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"records": history_service.history_store.list()},
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "model": config.GROQ_MODEL,
            "database_url_set": bool(config.DATABASE_URL),
            "db_path": str(config.DB_PATH),
            "groq_key_set": bool(config.GROQ_API_KEY),
        },
    )
