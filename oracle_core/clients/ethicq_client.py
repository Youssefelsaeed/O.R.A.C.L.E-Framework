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


async def evaluate_decision(
    client: httpx.AsyncClient,
    base_url: str,
    *,
    qauthcore_token: str,
    auth_context: Dict[str, Any],
    target_ip: str,
    source_ip: str,
    risk_score: float,
    risk_label: str,
    confidence_band: str,
    flow_id: str,
    threat_type: str,
    correlation_id: str,
) -> Tuple[Optional[str], Optional[float], Optional[Dict[str, Any]], Dict[str, Any]]:
    """Call EthicQ /api/v1/decisions/evaluate."""
    url = f"{base_url.rstrip('/')}/api/v1/decisions/evaluate"
    body: Dict[str, Any] = {
        "threat_alert": {
            "target_ip": target_ip,
            "source_ip": source_ip,
            "proposed_action": "block",
            "threat_level": risk_score,
            "risk_score": risk_score,
            "risk_label": risk_label,
            "confidence_band": confidence_band,
            "flow_id": flow_id,
            "threat_type": threat_type,
            "attack_family": threat_type,
            "correlation_id": correlation_id,
        },
        "qauthcore_token": qauthcore_token,
        "auth_context": auth_context,
        "correlation_id": correlation_id,
    }
    retry_meta = empty_retry_meta()

    async def _call() -> Tuple[Optional[str], Optional[float], Optional[Dict[str, Any]]]:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data.get("action"), data.get("confidence"), data

    try:
        result, retry_meta = await with_bounded_retry("ethicq", _call)
        return (*result, retry_meta)
    except RetryExhausted as exc:
        retry_meta = exc.meta
        cause = exc.cause
        if isinstance(cause, httpx.HTTPStatusError):
            reason = _exhausted_reason(f"http_{cause.response.status_code}", retry_meta)
            return None, None, {"reason": reason, "error": reason, "body": cause.response.text[:500], **retry_meta}, retry_meta
        if isinstance(cause, httpx.RequestError):
            reason = _exhausted_reason(f"request_error:{cause!s}", retry_meta)
            return None, None, {"reason": reason, "error": reason, **retry_meta}, retry_meta
        raise
