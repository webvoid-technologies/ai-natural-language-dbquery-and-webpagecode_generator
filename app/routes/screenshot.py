"""Screenshot to HTML/CSS routes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services import screenshot_service

logger = logging.getLogger(__name__)
router = APIRouter()

# In-process storage for the latest uploaded image and generated preview.
_state: dict[str, Any] = {
    "image_path": None,
    "html": "",
    "css": "",
    "standalone_html": "",
}


def _set_state(image_path: Path | None, generated: dict[str, Any] | None = None) -> None:
    _state["image_path"] = str(image_path) if image_path else None
    if generated:
        _state["html"] = generated.get("html", "")
        _state["css"] = generated.get("css", "")
        _state["standalone_html"] = generated.get("standalone_html", "")


@router.post("/webpage/upload")
async def upload_screenshot(file: UploadFile = File(...)) -> dict[str, str]:
    """Validate and store a screenshot upload."""
    try:
        contents = await file.read()
        screenshot_service.validate_screenshot(file.content_type or "", len(contents))
        path = screenshot_service.save_screenshot(
            contents, file.filename or "upload.png", content_type=file.content_type or ""
        )
        _set_state(path)
        return {"image_url": f"/static/uploads/{path.name}", "filename": path.name}
    except screenshot_service.ScreenshotServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        await file.close()


@router.post("/webpage/generate")
async def generate_webpage() -> dict[str, Any]:
    """Generate HTML/CSS from the last uploaded screenshot."""
    image_path = _state.get("image_path")
    if not image_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload a screenshot first.",
        )
    try:
        generated = await screenshot_service.generate_html_css(Path(image_path))
        _set_state(Path(image_path), generated)
        return {
            "html": generated["html"],
            "css": generated["css"],
            "preview_url": "/preview",
            "method": generated.get("method", "vision"),
        }
    except screenshot_service.ScreenshotServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    finally:
        # Clean up uploaded screenshot after processing.
        if image_path:
            screenshot_service.delete_screenshot(Path(image_path))
            _state["image_path"] = None


@router.get("/preview")
async def preview_generated() -> str:
    """Return the latest generated standalone HTML for iframe preview."""
    if not _state.get("standalone_html"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No generated webpage found. Upload and generate first.",
        )
    return _state["standalone_html"]
