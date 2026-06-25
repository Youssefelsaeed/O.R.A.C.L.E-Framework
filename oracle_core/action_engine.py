from __future__ import annotations

import logging
from typing import Any

import httpx

from .clients.ghosttunnel_client import transmit_oracle_trace
from .config import get_settings
from .models.oracle_event import OracleEvent


logger = logging.getLogger("oracle_core.action")


class ActionEngine:
    """Execute side-effects for OracleCore actions."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._client = http_client
        self._settings = get_settings()

    async def execute(self, event: OracleEvent) -> float:
        """Execute the action described by event.action.final_action.

        Returns GhostTunnel call duration in ms (0 if not invoked).
        """
        import time

        ghosttunnel_ms = 0.0
        final_action = (event.action.final_action or "").lower()
        risk = event.detection.risk_score
        confidence = event.ethics.confidence or 0.0
        requires_review = event.ethics.requires_human_review

        if requires_review:
            logger.info(
                {
                    "msg": "HUMAN REVIEW REQUIRED",
                    "trace_id": event.oracle_trace_id,
                    "final_action": final_action,
                    "risk_score": risk,
                    "ethics_confidence": confidence,
                }
            )
            return ghosttunnel_ms

        if final_action == "block" and confidence > 0.8:
            logger.info(
                {
                    "msg": "STRONG BLOCK simulated",
                    "trace_id": event.oracle_trace_id,
                    "risk_score": risk,
                    "ethics_confidence": confidence,
                }
            )
            return ghosttunnel_ms

        if final_action == "investigate":
            gt_start = time.perf_counter()
            ok, gt_resp = await transmit_oracle_trace(
                self._client,
                str(self._settings.ghosttunnel_url),
                oracle_trace_id=event.oracle_trace_id,
                flow_id=event.network.flow_id,
                risk_score=event.detection.risk_score,
                attack_family=event.detection.attack_family,
                correlation_id=event.oracle_trace_id,
            )
            ghosttunnel_ms = (time.perf_counter() - gt_start) * 1000.0
            if ok and gt_resp:
                accepted = bool(gt_resp.get("accepted", False))
                event.action.transmit_job_id = gt_resp.get("transmit_job_id") or gt_resp.get("packet_id")
                event.action.transmit_status = str(gt_resp.get("status", "queued"))
                raw_assurance = gt_resp.get("assurance_state")
                event.action.ghosttunnel_assurance_state = (
                    str(raw_assurance)
                    if raw_assurance is not None
                    else ("provisional" if accepted else None)
                )
                if event.assurance_states:
                    event.assurance_states.ghosttunnel_entropy_source = str(
                        gt_resp.get("entropy_source", "unknown")
                    )
                    event.assurance_states.ghosttunnel_assurance_state = event.action.ghosttunnel_assurance_state
                logger.info(
                    {
                        "msg": "INVESTIGATE routed via GhostTunnel",
                        "trace_id": event.oracle_trace_id,
                        "ghosttunnel_response": gt_resp,
                        "transmit_job_id": event.action.transmit_job_id,
                        "fast_ack": accepted,
                    }
                )
            else:
                logger.error(
                    {
                        "msg": "GhostTunnel transmit failed",
                        "trace_id": event.oracle_trace_id,
                        "error": gt_resp,
                    }
                )
            return ghosttunnel_ms

        # Default: allow / no-op
        logger.info(
            {
                "msg": "ALLOW / no-op",
                "trace_id": event.oracle_trace_id,
                "final_action": final_action,
            }
        )
        return ghosttunnel_ms

