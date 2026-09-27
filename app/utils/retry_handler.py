"""Generic retry helpers."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def async_retry(
    retries: int = 3,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    delay: float = 0.5,
    backoff: float = 1.5,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for retrying an async function on specified exceptions."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt_delay = delay
            last_exception: BaseException | None = None
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    logger.warning("Retry %d/%d for %s: %s", attempt, retries, func.__name__, exc)
                    if attempt < retries:
                        await asyncio.sleep(attempt_delay)
                        attempt_delay *= backoff
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


class RetryResult:
    """Simple container for a retried operation result."""

    def __init__(self, value: Any = None, attempts: int = 0, success: bool = False, error: str | None = None):
        self.value = value
        self.attempts = attempts
        self.success = success
        self.error = error
