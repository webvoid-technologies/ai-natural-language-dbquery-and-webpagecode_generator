"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
# Vision-capable model used by the screenshot -> HTML/CSS module
# (gpt-oss-120b is text-only and cannot accept image input).
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
GROQ_TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "60"))
GROQ_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "3"))

# Local SQLite database living inside app/database/ — no external DB needed.
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "database" / "college.db")))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(15 * 1024 * 1024)))  # 15 MB
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SQL_MAX_RETRIES = int(os.getenv("SQL_MAX_RETRIES", "5"))
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")

APP_NAME = "AI Natural Language Database Query & Webpage Code Generator"
APP_VERSION = "1.0.0"


def is_configured() -> dict[str, bool]:
    """Return configuration health flags for dashboard display."""
    return {
        "groq": bool(GROQ_API_KEY),
        "database": bool(DATABASE_URL),
    }
