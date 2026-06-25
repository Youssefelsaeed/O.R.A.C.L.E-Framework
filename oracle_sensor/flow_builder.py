from __future__ import annotations

import logging
import uuid
from typing import Dict

from .feature_extractor import extract_features
from .mutantshield_client import predict_decision


logger = logging.getLogger("oracle_sensor.flow")


def build_flow(packet_meta: Dict[str, object]) -> Dict[str, object]:
    """
    Convert basic packet metadata into a simplified MutantShield-style flow.

    packet_meta should contain at least: src_ip, dst_ip.
    """
    flow_id = str(uuid.uuid4())
    src_ip = str(packet_meta.get("src_ip", "0.0.0.0"))
    dst_ip = str(packet_meta.get("dst_ip", "0.0.0.0"))

    features = extract_features(packet_meta)
    decision_object, raw_result = predict_decision(features)

    flow = {
        "flow_id": flow_id,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "risk_score": float(decision_object.get("risk_score", 0.0)),
        "risk_label": str(decision_object.get("risk_label", "LOW")),
        "is_attack": bool(decision_object.get("is_attack", False)),
        "attack_family": str(decision_object.get("attack_family", "unknown")),
        "confidence_band": str(decision_object.get("confidence_band", "LOW")),
        "model_consensus": str(decision_object.get("model_consensus", "0/0")),
    }

    logger.info(
        {
            "msg": "mutantshield_inference",
            "features": features,
            "raw_model_outputs": raw_result,
            "final_fused_decision": decision_object,
        }
    )

    return flow

