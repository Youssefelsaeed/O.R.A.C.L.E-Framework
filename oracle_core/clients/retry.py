"""Bounded retry with jitter for idempotent-safe Oracle Core HTTP clients."""
from __future__ import annotations

import asyncio
import random
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

T = TypeVar("T")

DEFAULT_MAX_ATTEMPTS = 4
DEFAULT_BASE_DELAY_S = 0.15
DEFAULT_JITTER_S = 0.1


class RetryExhausted(Exception):
    def __init__(self, cause: BaseException, meta: Dict[str, Any]):
        super().__init__(str(cause))
        self.cause = cause
        self.meta = meta


def empty_retry_meta() -> Dict[str, Any]:
    return {"retry_count": 0, "retry_service": None, "retry_reason": None}


def merge_retry_meta(target: Dict[str, Any], meta: Dict[str, Any]) -> None:
    count = int(meta.get("retry_count") or 0)
    if count <= 0:
        return
    prev = int(target.get("retry_count") or 0)
    if count >= prev:
        target["retry_count"] = count
        target["retry_service"] = meta.get("retry_service")
        target["retry_reason"] = meta.get("retry_reason")


def _retry_delay(
    attempt: int,
    exc: BaseException,
    *,
    base_delay_s: float,
    jitter_s: float,
) -> float:
    import httpx

    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        retry_after = exc.response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(60.0, float(retry_after) + random.uniform(0, jitter_s))
            except ValueError:
                pass
        return min(5.0, base_delay_s * (2 ** attempt) * 4) + random.uniform(0, jitter_s)
    return base_delay_s * (attempt + 1) + random.uniform(0, jitter_s)


async def with_bounded_retry(
    service: str,
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay_s: float = DEFAULT_BASE_DELAY_S,
    jitter_s: float = DEFAULT_JITTER_S,
    is_retryable: Optional[Callable[[BaseException], bool]] = None,
) -> tuple[T, Dict[str, Any]]:
    """
    Run an async operation with bounded exponential backoff + jitter.

    Retries only on retryable transport/server-pressure errors by default.
    """
    retryable = is_retryable or _default_retryable
    retry_count = 0
    last_reason: Optional[str] = None

    for attempt in range(max_attempts):
        try:
            result = await operation()
            meta = {
                "retry_count": retry_count,
                "retry_service": service if retry_count else None,
                "retry_reason": last_reason if retry_count else None,
            }
            return result, meta
        except Exception as exc:
            if attempt >= max_attempts - 1 or not retryable(exc):
                meta = {
                    "retry_count": retry_count,
                    "retry_service": service if retry_count else None,
                    "retry_reason": last_reason or f"{type(exc).__name__}:{exc!s}",
                }
                raise RetryExhausted(exc, meta) from exc
            retry_count += 1
            last_reason = f"{type(exc).__name__}:{exc!s}"
            delay = _retry_delay(attempt, exc, base_delay_s=base_delay_s, jitter_s=jitter_s)
            await asyncio.sleep(delay)

    raise RuntimeError("retry_loop_exhausted")


def _default_retryable(exc: BaseException) -> bool:
    import httpx

    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        return code in (408, 429, 500, 502, 503, 504)
    return False
