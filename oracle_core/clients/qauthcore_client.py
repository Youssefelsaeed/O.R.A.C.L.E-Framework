from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import httpx
import logging

from .retry import RetryExhausted, empty_retry_meta, with_bounded_retry

logger = logging.getLogger(__name__)


def _exhausted_reason(prefix: str, retry_meta: Dict[str, Any]) -> str:
    if int(retry_meta.get("retry_count") or 0) >= 1:
        return f"retries_exhausted:{prefix}"
    return prefix


async def generate_token(
    client: httpx.AsyncClient,
    base_url: str,
    *,
    token_profile: str,
    metadata: Dict[str, Any],
    src_ip: str,
    dst_ip: str,
    flow_id: str,
) -> Tuple[Optional[str], Optional[float], Optional[Dict[str, Any]], Dict[str, Any]]:
    """Call Q-AuthCore /api/v1/tokens/generate."""
    url = f"{base_url.rstrip('/')}/api/v1/tokens/generate"
    body: Dict[str, Any] = {
        "token_profile": token_profile,
        "metadata": metadata,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "flow_id": flow_id,
    }
    retry_meta = empty_retry_meta()

    async def _call() -> Tuple[Optional[str], Optional[float], Optional[Dict[str, Any]]]:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data.get("token"), data.get("timestamp"), data

    try:
        result, retry_meta = await with_bounded_retry("qauthcore", _call)
        return (*result, retry_meta)
    except RetryExhausted as exc:
        retry_meta = exc.meta
        cause = exc.cause
        if isinstance(cause, httpx.HTTPStatusError):
            reason = _exhausted_reason(f"http_{cause.response.status_code}", retry_meta)
            return (
                None,
                None,
                {"error": reason, "body": cause.response.text[:500], **retry_meta},
                retry_meta,
            )
        if isinstance(cause, httpx.RequestError):
            reason = _exhausted_reason(f"request_error:{cause!s}", retry_meta)
            return None, None, {"error": reason, **retry_meta}, retry_meta
        raise


async def verify_token(
    client: httpx.AsyncClient,
    base_url: str,
    *,
    token: str,
    timestamp: float,
    src_ip: str,
    dst_ip: str,
    flow_id: str,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]], Dict[str, Any]]:
    """Call Q-AuthCore /api/v1/tokens/verify."""
    url = f"{base_url.rstrip('/')}/api/v1/tokens/verify"
    body: Dict[str, Any] = {
        "token": token,
        "timestamp": float(timestamp),
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "flow_id": flow_id,
    }
    retry_meta = empty_retry_meta()

    async def _call() -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("valid", False)), data.get("trust_level"), data

    try:
        result, retry_meta = await with_bounded_retry("qauthcore", _call)
        return (*result, retry_meta)
    except RetryExhausted as exc:
        retry_meta = exc.meta
        cause = exc.cause
        if isinstance(cause, httpx.HTTPStatusError):
            reason = _exhausted_reason(f"http_{cause.response.status_code}", retry_meta)
            return (
                False,
                None,
                {"reason": reason, "error": reason, "body": cause.response.text[:500], **retry_meta},
                retry_meta,
            )
        if isinstance(cause, httpx.RequestError):
            reason = _exhausted_reason(f"request_error:{cause!s}", retry_meta)
            return False, None, {"reason": reason, "error": reason, **retry_meta}, retry_meta
        raise
