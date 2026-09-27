"""Handle screenshot uploads and HTML/CSS generation with Groq."""

from __future__ import annotations

import logging
import mimetypes
import re
import uuid
from pathlib import Path
from typing import Any

from PIL import Image

from app import config
from app.services import groq_service, prompts

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg"}
MAX_DIMENSION = 2048


class ScreenshotServiceError(RuntimeError):
    """Raised when screenshot processing fails."""


def validate_screenshot(content_type: str, size: int) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ScreenshotServiceError(f"Unsupported file type: {content_type}. Only PNG/JPG/JPEG allowed.")
    if size > config.MAX_UPLOAD_SIZE:
        mb = config.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise ScreenshotServiceError(f"File exceeds maximum size of {mb:.0f} MB.")


def sanitize_filename(filename: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(filename).name)
    ext = Path(base).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg"}:
        ext = ".png"
    return f"{uuid.uuid4().hex}{ext}"


def _resize_if_needed(path: Path) -> Path:
    try:
        with Image.open(path) as img:
            if max(img.size) > MAX_DIMENSION:
                img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
                img.save(path, optimize=True)
    except Exception as exc:
        logger.warning("Could not resize image: %s", exc)
    return path


def save_screenshot(file_bytes: bytes, filename: str, content_type: str | None = None) -> Path:
    if content_type is None:
        content_type = mimetypes.guess_type(filename)[0] or ""
    validate_screenshot(content_type, len(file_bytes))
    safe_name = sanitize_filename(filename)
    path = config.UPLOAD_DIR / safe_name
    path.write_bytes(file_bytes)
    _resize_if_needed(path)
    return path


def delete_screenshot(path: Path | str | None) -> None:
    if not path:
        return
    p = Path(path)
    try:
        if p.exists():
            p.unlink()
    except OSError as exc:
        logger.warning("Could not delete uploaded screenshot %s: %s", p, exc)


def parse_html_css(content: str) -> dict[str, Any]:
    """Extract HTML and CSS code blocks from the LLM response."""
    blocks = re.findall(r"```(\w*)[^\n]*\n([\s\S]*?)```", content)
    html = css = ""
    for lang, body in blocks:
        lang = lang.lower()
        if lang == "html" and not html:
            html = body.strip()
        elif lang == "css" and not css:
            css = body.strip()
    # Positional fallback for unlabeled blocks: first = HTML, second = CSS.
    if not html and blocks:
        html = blocks[0][1].strip()
    if not css and len(blocks) >= 2:
        css = blocks[1][1].strip()
    if html:
        return {"html": html, "css": css}

    # Fallback: split by headings.
    parts = re.split(r"\n#{1,6}\s*(?:HTML|CSS)\s*\n", content, flags=re.IGNORECASE)
    if len(parts) >= 3:
        return {"html": parts[1].strip(), "css": parts[2].strip()}

    return {"html": content, "css": ""}


def _separate_html_css(html: str, css: str) -> dict[str, str]:
    """Guarantee clean separation: markup only in html, all styling in css."""
    # Rescue CSS the model embedded in <style> tags instead of the CSS block.
    embedded = re.findall(r"<style[^>]*>([\s\S]*?)</style>", html, flags=re.IGNORECASE)
    if embedded and not css.strip():
        css = "\n\n".join(block.strip() for block in embedded if block.strip())

    # Strip embedded styling out of the markup.
    html = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html, flags=re.IGNORECASE)
    html = re.sub(r'\s+style="[^"]*"', "", html, flags=re.IGNORECASE)
    html = re.sub(r"\s+style='[^']*'", "", html, flags=re.IGNORECASE)

    # Ensure the document links the external stylesheet.
    if "<html" in html.lower() and "stylesheet" not in html.lower():
        link = '<link rel="stylesheet" href="style.css">'
        if re.search(r"</head>", html, flags=re.IGNORECASE):
            html = re.sub(r"</head>", f"  {link}\n</head>", html, count=1, flags=re.IGNORECASE)
        else:
            html = link + "\n" + html

    return {"html": html.strip(), "css": css.strip()}


def _ensure_standalone_html(html: str, css: str) -> str:
    """Return a complete HTML document with embedded CSS for iframe preview."""
    if "<html" in html.lower():
        if css.strip() and "<style" not in html.lower():
            embedded = f"<style>\n{css}\n</style>"
            if re.search(r"<link[^>]*stylesheet[^>]*>", html, flags=re.IGNORECASE):
                return re.sub(r"<link[^>]*stylesheet[^>]*>", embedded, html, count=1, flags=re.IGNORECASE)
            if re.search(r"</head>", html, flags=re.IGNORECASE):
                return re.sub(r"</head>", f"{embedded}\n</head>", html, count=1, flags=re.IGNORECASE)
            return embedded + html
        return html
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Generated Preview</title>
<style>{css}</style>
</head>
<body>
{html}
</body>
</html>"""


def analyze_image(image_path: Path) -> dict[str, Any]:
    """Extract local features (palette, size, OCR text) for the non-vision fallback."""
    meta: dict[str, Any] = {"width": 0, "height": 0, "palette": [], "text": ""}
    try:
        with Image.open(image_path) as img:
            meta["width"], meta["height"] = img.size
            small = img.convert("RGB").resize((64, 64))
            quantized = small.quantize(colors=6, method=Image.MEDIANCUT)
            palette = quantized.getpalette() or []
            meta["palette"] = [
                "#{:02x}{:02x}{:02x}".format(*palette[i:i + 3])
                for i in range(0, min(18, len(palette)), 3)
            ]
    except Exception as exc:
        logger.warning("Image analysis failed: %s", exc)

    try:
        import pytesseract

        if config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
        with Image.open(image_path) as img:
            meta["text"] = (pytesseract.image_to_string(img) or "")[:2000]
    except Exception:
        logger.info("OCR unavailable; continuing without extracted text")
    return meta


async def _generate_with_text_model(image_path: Path) -> str:
    """Fallback for Groq accounts without vision models: analyze locally, then prompt."""
    meta = analyze_image(image_path)
    user_prompt = (
        "Analyze this webpage screenshot indirectly using extracted features and "
        "recreate a responsive webpage.\n\n"
        f"Image size: {meta['width']}x{meta['height']} px\n"
        f"Dominant colors: {', '.join(meta['palette']) or 'unknown'}\n"
        f"Visible text extracted by OCR:\n{meta['text'] or '(none)'}\n\n"
        "Infer the most likely layout (nav, hero, cards, buttons, footer) and produce "
        "a polished, responsive HTML5 + CSS3 recreation using those colors and text."
    )
    return await groq_service.get_service().generate_text(
        system_prompt=prompts.SCREENSHOT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.4,
        max_tokens=4096,
    )


async def generate_html_css(image_path: Path) -> dict[str, Any]:
    method = "vision"
    try:
        content = await groq_service.get_service().generate_vision(
            system_prompt=prompts.SCREENSHOT_SYSTEM_PROMPT,
            user_text=prompts.SCREENSHOT_USER_PROMPT,
            image_path=image_path,
            temperature=0.3,
            max_tokens=4096,
            model=config.GROQ_VISION_MODEL,
        )
    except groq_service.GroqServiceError as exc:
        logger.warning("Vision model unavailable (%s); falling back to text analysis", exc)
        method = "fallback"
        try:
            content = await _generate_with_text_model(image_path)
        except groq_service.GroqServiceError as fallback_exc:
            raise ScreenshotServiceError(
                f"Groq could not generate code: {fallback_exc}"
            ) from fallback_exc

    parsed = parse_html_css(content)
    separated = _separate_html_css(parsed["html"], parsed["css"])
    standalone = _ensure_standalone_html(separated["html"], separated["css"])
    return {
        "html": separated["html"],
        "css": separated["css"],
        "standalone_html": standalone,
        "method": method,
    }
