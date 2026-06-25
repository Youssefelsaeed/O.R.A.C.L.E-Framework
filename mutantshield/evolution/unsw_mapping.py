"""UNSW-NB15 → CIC-IDS2017 semantic feature mapping for fair evaluation."""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# CIC feature -> UNSW column (from production MutantShield trial mapping)
UNSW_TO_CIC_FEATURE_MAP: Dict[str, str] = {
    "Destination Port": "ct_dst_sport_ltm",
    "Flow Duration": "dur",
    "Total Fwd Packets": "spkts",
    "Total Backward Packets": "dpkts",
    "Total Length of Fwd Packets": "sbytes",
    "Total Length of Bwd Packets": "dbytes",
    "Fwd Packet Length Max": "sbytes",
    "Fwd Packet Length Min": "sbytes",
    "Fwd Packet Length Mean": "smean",
    "Fwd Packet Length Std": "sjit",
    "Bwd Packet Length Max": "dbytes",
    "Bwd Packet Length Min": "dbytes",
    "Bwd Packet Length Mean": "dmean",
    "Bwd Packet Length Std": "djit",
    "Flow Bytes/s": "rate",
    "Flow Packets/s": "rate",
    "Flow IAT Mean": "sinpkt",
    "Flow IAT Std": "sjit",
    "Flow IAT Max": "sinpkt",
    "Flow IAT Min": "dinpkt",
    "Fwd IAT Total": "sinpkt",
    "Fwd IAT Mean": "sinpkt",
    "Fwd IAT Std": "sjit",
    "Bwd IAT Mean": "dinpkt",
    "Bwd IAT Std": "djit",
    "Init_Win_bytes_forward": "swin",
    "Init_Win_bytes_backward": "dwin",
    "Subflow Fwd Packets": "spkts",
    "Subflow Bwd Packets": "dpkts",
    "Subflow Fwd Bytes": "sbytes",
    "Subflow Bwd Bytes": "dbytes",
    "Down/Up Ratio": "dload",
    "Average Packet Size": "smean",
    "Avg Fwd Segment Size": "smean",
    "Avg Bwd Segment Size": "dmean",
    "Min Packet Length": "sloss",
    "Max Packet Length": "dloss",
    "Packet Length Mean": "smean",
    "Packet Length Std": "sjit",
}


def mapping_quality(feature_names: List[str]) -> Tuple[str, int, int]:
    """Return (quality_label, mapped_count, zero_fill_count)."""
    mapped = sum(1 for f in feature_names if f in UNSW_TO_CIC_FEATURE_MAP)
    zero_fill = len(feature_names) - mapped
    ratio = mapped / max(1, len(feature_names))
    if ratio >= 0.35:
        quality = "good"
    elif ratio >= 0.15:
        quality = "partial"
    else:
        quality = "poor"
    return quality, mapped, zero_fill


def unsw_row_to_cic_features(row: pd.Series, feature_names: List[str]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for feat in feature_names:
        unsw_col = UNSW_TO_CIC_FEATURE_MAP.get(feat)
        if unsw_col and unsw_col in row.index:
            val = row[unsw_col]
            if pd.isna(val) or (isinstance(val, float) and (np.isinf(val) or abs(val) > 1e15)):
                out[feat] = 0.0
            else:
                out[feat] = float(val)
        else:
            out[feat] = 0.0
    return out


def is_unsw_benign(label: str) -> bool:
    s = str(label).strip().lower()
    return s in ("normal", "benign", "0")
