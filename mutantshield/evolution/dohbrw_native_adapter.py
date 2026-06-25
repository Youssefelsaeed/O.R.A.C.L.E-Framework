"""Native DoHBrw feature helpers for candidate-only anomaly adapters."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

NATIVE_DOHBRW_FEATURES: List[str] = [
    "FlowBytesSent",
    "FlowSentRate",
    "FlowBytesReceived",
    "FlowReceivedRate",
    "PacketLengthVariance",
    "PacketLengthStandardDeviation",
    "PacketLengthMean",
    "PacketLengthMedian",
    "PacketLengthMode",
    "PacketLengthSkewFromMedian",
    "PacketLengthSkewFromMode",
    "PacketLengthCoefficientofVariation",
    "PacketTimeVariance",
    "PacketTimeStandardDeviation",
    "PacketTimeMean",
    "PacketTimeMedian",
    "PacketTimeMode",
    "PacketTimeSkewFromMedian",
    "PacketTimeSkewFromMode",
    "PacketTimeCoefficientofVariation",
    "ResponseTimeTimeVariance",
    "ResponseTimeTimeStandardDeviation",
    "ResponseTimeTimeMean",
    "ResponseTimeTimeMedian",
    "ResponseTimeTimeMode",
    "ResponseTimeTimeSkewFromMedian",
    "ResponseTimeTimeSkewFromMode",
    "ResponseTimeTimeCoefficientofVariation",
]

CLIP_MIN = -1e9
CLIP_MAX = 1e9


def find_dohbrw_files(path: Path) -> List[Path]:
    if path.is_file() and path.suffix.lower() in {".csv", ".parquet"}:
        return [path]
    files = list(path.rglob("*.csv")) + list(path.rglob("*.parquet")) if path.exists() else []
    return sorted(files, key=lambda p: (0 if "archive" in str(p).lower() else 1, -p.stat().st_size))


def label_column(columns: List[str]) -> Optional[str]:
    lowered = {str(c).strip().lower(): str(c).strip() for c in columns}
    for candidate in ("label", "class", "traffic_type", "trafficcategory", "anomaly"):
        if candidate in lowered:
            return lowered[candidate]
    return None


def normalize_label(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return "unlabeled"
    lowered = text.lower()
    if lowered in {"benign", "normal", "non-doh", "nondoh"}:
        return "benign"
    if "benign" in lowered and "malicious" not in lowered:
        return "benign"
    return "anomaly"


def sanitize_numeric(value: Any) -> Tuple[float, Optional[str]]:
    try:
        number = float(value)
    except Exception:
        return 0.0, "non_numeric"
    if math.isnan(number):
        return 0.0, "nan"
    if math.isinf(number):
        return (CLIP_MAX if number > 0 else CLIP_MIN), "inf"
    clipped = min(max(number, CLIP_MIN), CLIP_MAX)
    if clipped != number:
        return clipped, "clipped"
    return float(clipped), None


def native_features_from_row(row: pd.Series, feature_names: Optional[List[str]] = None) -> Tuple[Dict[str, float], Dict[str, Any]]:
    feature_names = feature_names or NATIVE_DOHBRW_FEATURES
    features: Dict[str, float] = {}
    missing: List[str] = []
    sanitization: Dict[str, int] = {}
    for feature in feature_names:
        if feature not in row:
            features[feature] = 0.0
            missing.append(feature)
            continue
        value, reason = sanitize_numeric(row.get(feature))
        if reason:
            sanitization[reason] = sanitization.get(reason, 0) + 1
        features[feature] = value
    quality = {
        "feature_count": len(feature_names),
        "mapped_count": len(feature_names) - len(missing),
        "missing_count": len(missing),
        "missing_features": missing,
        "mapped_ratio": round((len(feature_names) - len(missing)) / max(1, len(feature_names)), 4),
        "sanitization_counts": sanitization,
    }
    return features, quality


def dataframe_to_native_matrix(df: pd.DataFrame, feature_names: Optional[List[str]] = None) -> pd.DataFrame:
    feature_names = feature_names or NATIVE_DOHBRW_FEATURES
    out = pd.DataFrame(index=df.index)
    for feature in feature_names:
        out[feature] = pd.to_numeric(df.get(feature, 0.0), errors="coerce").fillna(0.0).clip(CLIP_MIN, CLIP_MAX)
    return out.astype(float)
