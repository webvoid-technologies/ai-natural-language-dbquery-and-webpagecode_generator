"""Centralized, reusable Groq client with timeout handling and retries."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from groq import AsyncGroq, APIError, APITimeoutError

from app import config

logger = logging.getLogger(__name__)


class GroqServiceError(RuntimeError):
    """Raised when the Groq API cannot complete a request."""


class GroqService:
    """Reusable async Groq service used by all AI features."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.api_key = api_key or config.GROQ_API_KEY
        self.model = model or config.GROQ_MODEL
        self.timeout = timeout or config.GROQ_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else config.GROQ_MAX_RETRIES

    def _client(self) -> AsyncGroq:
        if not self.api_key:
            raise GroqServiceError("GROQ_API_KEY is not configured on the server.")
        return AsyncGroq(api_key=self.api_key, timeout=self.timeout)

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format: dict[str, str] | None = None,
        model: str | None = None,
    ) -> str:
        """Call Groq chat completions with retries and timeout handling."""
        parameters: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            parameters["response_format"] = response_format

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                client = self._client()
                response = await client.chat.completions.create(**parameters)
                content = response.choices[0].message.content
                if not content:
                    raise GroqServiceError("Groq returned an empty response.")
                return content
            except (APIError, APITimeoutError, TimeoutError) as exc:
                last_error = exc
                logger.warning("Groq attempt %d/%d failed: %s", attempt, self.max_retries, exc)
            except Exception as exc:
                logger.exception("Unexpected Groq error")
                raise GroqServiceError(f"Groq request failed: {exc}") from exc

        raise GroqServiceError(
            f"Groq failed after {self.max_retries} retries: {last_error}"
        ) from last_error

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format: dict[str, str] | None = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.chat_completion(messages, temperature, max_tokens, response_format)

    async def generate_vision(
        self,
        system_prompt: str,
        user_text: str,
        image_path: Path,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> str:
        """Send a prompt with a base64-encoded image for vision-capable models."""
        image_data = image_path.read_bytes()
        encoded = base64.b64encode(image_data).decode("utf-8")
        ext = image_path.suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in {"jpg", "jpeg"} else "image/png"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
                ],
            },
        ]
        return await self.chat_completion(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model or config.GROQ_VISION_MODEL,
        )


_service: GroqService | None = None


def get_service() -> GroqService:
    global _service
    if _service is None:
        _service = GroqService()
    return _service
