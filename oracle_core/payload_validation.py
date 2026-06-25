"""Validate /oracle/process payloads before orchestrator execution."""
from __future__ import annotations

import ipaddress
from typing import Any, Dict, List, Tuple

MAX_PAYLOAD_BYTES = 256_000
MAX_FLOW_ID_LEN = 256


def _is_valid_ip(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def _coerce_float(value: Any) -> Tuple[bool, float | None]:
    if value is None:
        return True, 0.0
    if isinstance(value, bool):
        return False, None
    if isinstance(value, (int, float)):
        return True, float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return True, 0.0
        try:
            return True, float(text)
        except ValueError:
            return False, None
    return False, None


def validate_oracle_payload(payload: Any) -> Tuple[bool, List[str]]:
    """Return (ok, detail_codes). Unknown extra fields are allowed."""
    details: List[str] = []

    if not isinstance(payload, dict):
        return False, ["payload_must_be_object"]

    # Rough size guard without serializing huge blobs twice.
    try:
        import json

        encoded = json.dumps(payload, default=str)
        if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            details.append("payload_too_large")
    except (TypeError, ValueError):
        details.append("payload_not_serializable")

    flow_id = payload.get("flow_id")
    if flow_id is None or str(flow_id).strip() == "":
        details.append("missing_flow_id")
    elif len(str(flow_id)) > MAX_FLOW_ID_LEN:
        details.append("flow_id_too_long")

    src_ip = payload.get("src_ip")
    if src_ip is None or str(src_ip).strip() == "":
        details.append("missing_src_ip")
    elif not _is_valid_ip(src_ip):
        details.append("invalid_src_ip")

    dst_ip = payload.get("dst_ip")
    if dst_ip is None or str(dst_ip).strip() == "":
        details.append("missing_dst_ip")
    elif not _is_valid_ip(dst_ip):
        details.append("invalid_dst_ip")

    if "risk_score" in payload:
        ok, _ = _coerce_float(payload.get("risk_score"))
        if not ok:
            details.append("invalid_risk_score_type")

    return len(details) == 0, details
