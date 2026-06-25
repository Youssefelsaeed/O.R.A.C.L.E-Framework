from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

import httpx
import logging

from .config import get_settings
from .clients.qauthcore_client import generate_token, verify_token
from .clients.ethicq_client import evaluate_decision
from .clients.chronoledger_client import log_security_event
from .action_engine import ActionEngine
from .clients.retry import merge_retry_meta
from .payload_validation import _coerce_float
from .models.oracle_event import (
    ActionContext,
    AuditContext,
    AuthContext,
    DetectionContext,
    EthicsContext,
    NetworkContext,
    OracleEvent,
    AssuranceStates,
    PipelineTimingsMs,
)


class OracleOrchestrator:
    """Coordinates calls between MutantShield, QAuthCore, EthicQ, and ChronoLedger."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._settings = get_settings()
        self._client = http_client
        self._action_engine = ActionEngine(http_client)

    async def process_mutantshield_event(self, payload: Dict[str, Any]) -> OracleEvent:
        """Main pipeline for /oracle/process."""
        req_start = time.perf_counter()
        print("ORACLE CORE NEW VERSION RUNNING")
        logging.getLogger(__name__).warning(
            {
                "msg": "orchestrator_entry",
                "version": "debug_v2",
            }
        )
        now = time.time()
        trace_id = str(uuid.uuid4())

        risk_ok, risk_value = _coerce_float(payload.get("risk_score", 0.0))
        if not risk_ok:
            raise ValueError("invalid_risk_score_type")

        network = NetworkContext(
            flow_id=str(payload.get("flow_id", "")),
            src_ip=str(payload.get("src_ip", "")),
            dst_ip=str(payload.get("dst_ip", "")),
        )

        detection = DetectionContext(
            risk_score=float(risk_value or 0.0),
            risk_label=str(payload.get("risk_label", "UNKNOWN")),
            is_attack=bool(payload.get("is_attack", False)),
            attack_family=str(payload.get("attack_family", "unknown")),
            confidence_band=str(payload.get("confidence_band", "unknown")),
            model_consensus=str(payload.get("model_consensus", "n/a")),
        )

        auth = AuthContext()
        ethics = EthicsContext()
        action = ActionContext()
        audit = AuditContext()

        event = OracleEvent(
            oracle_trace_id=trace_id,
            timestamp=now,
            network=network,
            detection=detection,
            auth=auth,
            ethics=ethics,
            action=action,
            audit=audit,
            assurance_states=AssuranceStates(),
        )

        logger = logging.getLogger(__name__)
        qauth_ms = 0.0
        ethicq_ms = 0.0
        chronoledger_ms = 0.0
        ghosttunnel_ms = 0.0
        retry_meta: Dict[str, Any] = {"retry_count": 0, "retry_service": None, "retry_reason": None}

        # === Step 1: QAuthCore token generation + verification (single trust authority) ===
        qauth_start = time.perf_counter()
        meta = {
            "source_module": "OracleCore",
            "event_type": "threat_detection",
            "trust_level": "high" if detection.is_attack else "medium",
            "src_ip": network.src_ip,
            "dst_ip": network.dst_ip,
            "flow_id": network.flow_id,
        }
        token, token_ts, auth_raw, qauth_gen_retry = await generate_token(
            self._client,
            str(self._settings.qauthcore_url),
            token_profile="relaxed",
            metadata=meta,
            src_ip=network.src_ip,
            dst_ip=network.dst_ip,
            flow_id=network.flow_id,
        )
        merge_retry_meta(retry_meta, qauth_gen_retry)
        if token is None or token_ts is None:
            auth_context = {
                "verified": False,
                "token": token,
                "timestamp": token_ts,
                "trust_level": "unverified",
            }
            event.auth.verified = False
            event.auth.status = "failed"
            event.auth.reason = (auth_raw or {}).get("error", "qauthcore_error")
            event.failed_services.append("qauthcore")
        else:
            event.auth.token = token
            event.auth.timestamp = float(token_ts)
            valid, trust_level, verify_raw, qauth_verify_retry = await verify_token(
                self._client,
                str(self._settings.qauthcore_url),
                token=token,
                timestamp=float(token_ts),
                src_ip=network.src_ip,
                dst_ip=network.dst_ip,
                flow_id=network.flow_id,
            )
            merge_retry_meta(retry_meta, qauth_verify_retry)
            auth_context = {
                "verified": bool(valid),
                "token": token,
                "timestamp": float(token_ts),
                "trust_level": trust_level or "standard",
            }
            logger.info({"msg": "auth_verified", "auth_context": auth_context})
            if not valid:
                event.auth.verified = False
                event.auth.status = "failed"
                event.auth.reason = (verify_raw or {}).get("reason") or (verify_raw or {}).get("error", "qauthcore_verify_failed")
                event.failed_services.append("qauthcore")
            else:
                event.auth.verified = True
                event.auth.status = "ok"
                event.auth.trust_level = auth_context["trust_level"]
        if event.assurance_states:
            old = event.assurance_states.qauth_assurance_state
            event.assurance_states.qauth_entropy_source = str((auth_raw or {}).get("entropy_source", "unknown"))
            event.assurance_states.qauth_assurance_state = str((auth_raw or {}).get("assurance_state", "quantum_verified" if event.auth.verified else "failed"))
            logger.info(
                {
                    "msg": "oracle_quantum_assurance_update",
                    "trace_id": trace_id,
                    "component": "qauthcore",
                    "old_state": old,
                    "new_state": event.assurance_states.qauth_assurance_state,
                    "latency_ms": round(qauth_ms, 2),
                }
            )
        qauth_ms = (time.perf_counter() - qauth_start) * 1000.0

        # === Step 2: EthicQ decision ===
        ethicq_start = time.perf_counter()
        ethics_raw: Optional[Dict[str, Any]] = None
        if event.auth.status == "ok" and event.auth.token and auth_context.get("verified"):
            action_label, confidence, ethics_raw, ethicq_retry = await evaluate_decision(
                self._client,
                str(self._settings.ethicq_url),
                qauthcore_token=event.auth.token,
                auth_context=auth_context,
                target_ip=network.dst_ip,
                source_ip=network.src_ip,
                risk_score=detection.risk_score,
                risk_label=detection.risk_label,
                confidence_band=detection.confidence_band,
                flow_id=network.flow_id,
                threat_type=detection.attack_family,
                correlation_id=trace_id,
            )
            merge_retry_meta(retry_meta, ethicq_retry)
            if action_label is None:
                ethics.reason = (ethics_raw or {}).get("reason") or (ethics_raw or {}).get("error", "ethicq_error")
                ethics.decision = "investigate"
                ethics.confidence = None
                event.failed_services.append("ethicq")
            else:
                ethics.decision = action_label
                ethics.confidence = confidence
                ethics.reason = None
                # EthicQ DecisionResponse has requires_human_review
                ethics.requires_human_review = bool(
                    (ethics_raw or {}).get("requires_human_review", False)
                )
        else:
            ethics.decision = "investigate"
            ethics.confidence = None
            ethics.reason = "untrusted_request"
            event.failed_services.append("ethicq")
        if event.assurance_states:
            old = event.assurance_states.ethicq_provenance_state
            event.assurance_states.ethicq_provenance_state = str((ethics_raw or {}).get("provenance_state", "verified" if ethics.decision else "unknown"))
            logger.info(
                {
                    "msg": "oracle_quantum_assurance_update",
                    "trace_id": trace_id,
                    "component": "ethicq",
                    "old_state": old,
                    "new_state": event.assurance_states.ethicq_provenance_state,
                    "latency_ms": round(ethicq_ms, 2),
                }
            )
        ethicq_ms = (time.perf_counter() - ethicq_start) * 1000.0

        # === Step 3: Determine final action ===
        final_action = ethics.decision or "investigate"
        action.final_action = final_action
        action.executed = False
        action.reason = ethics.reason

        # === Step 4: ChronoLedger logging (best-effort) ===
        if event.auth.token and event.auth.timestamp is None:
            logging.getLogger(__name__).error(
                {"msg": "chronoledger_skipped_missing_timestamp"}
            )
            audit.logged = False
            audit.reason = "missing_qauthcore_timestamp"
            event.failed_services.append("chronoledger")
        elif not auth_context.get("verified"):
            audit.logged = False
            audit.reason = "untrusted_request"
            event.failed_services.append("chronoledger")
        else:
            chrono_start = time.perf_counter()
            logged, event_id, audit_raw, chrono_retry = await log_security_event(
                self._client,
                str(self._settings.chronoledger_url),
                oracle_trace_id=trace_id,
                event_timestamp=now,
                flow_id=network.flow_id,
                source_ip=network.src_ip,
                dest_ip=network.dst_ip,
                detection_payload=detection.model_dump(),
                ethics_decision=ethics.decision,
                ethics_confidence=ethics.confidence,
                source_module="OracleCore",
                qauthcore_token=event.auth.token or "",
                qauthcore_timestamp=float(event.auth.timestamp or 0.0),
                auth_context=auth_context,
            )
            merge_retry_meta(retry_meta, chrono_retry)
            chronoledger_ms = (time.perf_counter() - chrono_start) * 1000.0
            audit.logged = logged
            audit.ledger_event_id = event_id
            if not logged:
                audit.reason = (audit_raw or {}).get("error", "chronoledger_error")
                event.failed_services.append("chronoledger")
            if event.assurance_states:
                old = event.assurance_states.chronoledger_assurance_state
                event.assurance_states.chronoledger_assurance_state = str((audit_raw or {}).get("assurance_state", "quantum_verified" if logged else "failed"))
                logger.info(
                    {
                        "msg": "oracle_quantum_assurance_update",
                        "trace_id": trace_id,
                        "component": "chronoledger",
                        "old_state": old,
                        "new_state": event.assurance_states.chronoledger_assurance_state,
                        "latency_ms": round(chronoledger_ms, 2),
                    }
                )

        # === Step 5: Action engine (best-effort, must not break pipeline) ===
        try:
            ghosttunnel_ms = await self._action_engine.execute(event)
            event.action.executed = True
        except Exception as exc:  # fail-safe: never let this break the pipeline
            event.action.executed = False
            if not event.action.reason:
                event.action.reason = f"action_engine_error:{exc!s}"
            print(
                f"[OracleCore] ActionEngine failed for trace_id={event.oracle_trace_id}: {exc!r}"
            )

        event.failed_services = sorted(set(event.failed_services))
        event.status = "degraded" if event.failed_services else "ok"
        total_ms = (time.perf_counter() - req_start) * 1000.0
        service_sum = qauth_ms + ethicq_ms + chronoledger_ms + ghosttunnel_ms
        oracle_overhead_ms = max(0.0, total_ms - service_sum)
        event.pipeline_timings_ms = PipelineTimingsMs(
            qauth_ms=round(qauth_ms, 2),
            ethicq_ms=round(ethicq_ms, 2),
            chronoledger_ms=round(chronoledger_ms, 2),
            ghosttunnel_ms=round(ghosttunnel_ms, 2),
            total_ms=round(total_ms, 2),
            oracle_overhead_ms=round(oracle_overhead_ms, 2),
            retry_count=int(retry_meta.get("retry_count") or 0),
            retry_service=retry_meta.get("retry_service"),
            retry_reason=retry_meta.get("retry_reason"),
        )
        logger.warning(
            {
                "msg": "oracle_pipeline_summary",
                "trace_id": event.oracle_trace_id,
                "status": event.status,
                "failed_services": event.failed_services,
                "latency_ms": round(total_ms, 2),
                "pipeline_timings_ms": event.pipeline_timings_ms.model_dump(),
                "auth_status": event.auth.status,
                "ethics_decision": event.ethics.decision,
                "audit_logged": event.audit.logged,
            }
        )

        return event

