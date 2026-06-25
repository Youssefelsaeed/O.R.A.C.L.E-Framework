from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)


async def transmit_oracle_trace(
    client: httpx.AsyncClient,
    base_url: str,
    *,
    oracle_trace_id: str,
    flow_id: str,
    risk_score: float,
    attack_family: str,
    correlation_id: str,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Send an OracleCore trace to GhostTunnel /api/v1/transmit.

    Returns (ok, raw_response_or_error_dict).
    """
    url = f"{base_url.rstrip('/')}/api/v1/transmit"
    body: Dict[str, Any] = {
        "data": {
            "trace_id": oracle_trace_id,
            "flow_id": flow_id,
            "risk_score": risk_score,
            "attack_family": attack_family,
        },
        "priority": "normal",
        "preferred_protocol": "http",
        "metadata": {
            "source": "oracle_core",
            "correlation_id": correlation_id,
            "oracle_trace_id": oracle_trace_id,
            "trace_id": oracle_trace_id,
        },
    }
    last_error: Optional[Dict[str, Any]] = None
    for attempt in range(3):
        try:
            logger.debug(
                {
                    "target_service": "ghosttunnel",
                    "url": url,
                    "payload": body,
                }
            )
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            return True, resp.json()
        except httpx.RequestError as exc:
            last_error = {"error": f"request_error:{exc!s}", "attempt": attempt + 1}
        except httpx.HTTPStatusError as exc:
            last_error = {
                "error": f"http_{exc.response.status_code}",
                "body": exc.response.text[:500],
                "attempt": attempt + 1,
            }
        if attempt < 2:
            await asyncio.sleep(0.2 * (attempt + 1))

    return False, last_error

