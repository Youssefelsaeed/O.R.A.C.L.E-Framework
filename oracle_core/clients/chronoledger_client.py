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


async def log_security_event(
    client: httpx.AsyncClient,
    base_url: str,
    *,
    oracle_trace_id: str,
    event_timestamp: float,
    flow_id: str,
    source_ip: str,
    dest_ip: str,
    detection_payload: Dict[str, Any],
    ethics_decision: Optional[str],
    ethics_confidence: Optional[float],
    source_module: str,
    qauthcore_token: str,
    qauthcore_timestamp: float,
    auth_context: Dict[str, Any],
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]], Dict[str, Any]]:
    """Call ChronoLedger /api/v1/events with idempotency metadata."""
    url = f"{base_url.rstrip('/')}/api/v1/events"
    body: Dict[str, Any] = {
        "event_type": "security_event",
        "data": {
            "trace_id": oracle_trace_id,
            "timestamp": event_timestamp,
            "flow_id": flow_id,
            "decision": ethics_decision,
            "risk_score": detection_payload.get("risk_score"),
            "source_ip": source_ip,
            "dest_ip": dest_ip,
            "detection": detection_payload,
            "ethics": {"decision": ethics_decision, "confidence": ethics_confidence},
            "auth_context": auth_context,
            "action": detection_payload.get("risk_label", "unknown"),
        },
        "source_module": source_module,
        "qauthcore_token": qauthcore_token,
        "auth_context": auth_context,
        "metadata": {
            "oracle_trace_id": oracle_trace_id,
            "idempotency_key": oracle_trace_id,
        },
        "qauthcore_timestamp": qauthcore_timestamp,
    }
    retry_meta = empty_retry_meta()

    async def _call() -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return True, data.get("event_id"), data

    try:
        result, retry_meta = await with_bounded_retry("chronoledger", _call)
        return (*result, retry_meta)
    except RetryExhausted as exc:
        retry_meta = exc.meta
        cause = exc.cause
        if isinstance(cause, httpx.HTTPStatusError):
            reason = _exhausted_reason(f"http_{cause.response.status_code}", retry_meta)
            return False, None, {"error": reason, "body": cause.response.text[:500], **retry_meta}, retry_meta
        if isinstance(cause, httpx.RequestError):
            reason = _exhausted_reason(f"request_error:{cause!s}", retry_meta)
            return False, None, {"error": reason, **retry_meta}, retry_meta
        raise
