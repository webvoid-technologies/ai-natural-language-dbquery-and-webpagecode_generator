"""FastAPI entry point for the AI Natural Language Database Query & Webpage Code Generator."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import database, history, pages, screenshot

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="AI Natural Language Database Query & Webpage Code Generator",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(pages.router)
app.include_router(database.router)
app.include_router(screenshot.router)
app.include_router(history.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "provider": "groq"}
