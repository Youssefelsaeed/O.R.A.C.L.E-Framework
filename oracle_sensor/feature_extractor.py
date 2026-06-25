from __future__ import annotations

import logging
from typing import Dict


logger = logging.getLogger("oracle_sensor.features")


# Core CIC-style fields commonly expected by MutantShield model bundles.
_CIC_BASE_FEATURES = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
]


def extract_features(packet_meta: Dict[str, object]) -> Dict[str, float]:
    """
    Extract packet features in a CIC-compatible dict shape.

    This ensures feature keys are close to what MutantShield XGBoost / AE / GNN
    pipelines expect, while still being derivable from single-packet metadata.
    """
    length = float(packet_meta.get("length", 0.0))
    protocol = float(packet_meta.get("protocol", 0.0))
    duration = 0.1
    pkt_count = 1.0

    # Best-effort synthetic rates from single packet.
    bytes_per_s = (length / duration) if duration > 0 else 0.0
    pkts_per_s = (pkt_count / duration) if duration > 0 else 0.0

    # Start with zeros for all known CIC-style base keys.
    features: Dict[str, float] = {k: 0.0 for k in _CIC_BASE_FEATURES}

    # Fill with packet-derived approximations.
    features.update(
        {
            "Destination Port": protocol,  # no L4 parse here; protocol used as proxy
            "Flow Duration": duration,
            "Total Fwd Packets": pkt_count,
            "Total Backward Packets": 0.0,
            "Total Length of Fwd Packets": length,
            "Total Length of Bwd Packets": 0.0,
            "Fwd Packet Length Max": length,
            "Fwd Packet Length Min": length,
            "Fwd Packet Length Mean": length,
            "Fwd Packet Length Std": 0.0,
            "Bwd Packet Length Max": 0.0,
            "Bwd Packet Length Min": 0.0,
            "Bwd Packet Length Mean": 0.0,
            "Bwd Packet Length Std": 0.0,
            "Flow Bytes/s": bytes_per_s,
            "Flow Packets/s": pkts_per_s,
            "Flow IAT Mean": duration,
            "Flow IAT Std": 0.0,
            "Flow IAT Max": duration,
            "Flow IAT Min": duration,
            # Extra generic fields requested by earlier sensor stages:
            "length": length,
            "protocol": protocol,
            "packet_count": pkt_count,
            "duration": duration,
        }
    )

    logger.debug({"msg": "features_extracted", "features": features})
    return features

