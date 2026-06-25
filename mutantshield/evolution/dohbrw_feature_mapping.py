"""Map DoHBrw aggregate flow features to MutantShield's production schema."""
from __future__ import annotations

import math
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .feature_mapping import CLIP_MAX, CLIP_MIN, load_production_features
from .reports import write_json


DIRECT_ALIASES: Dict[str, str] = {
    "FlowBytesSent": "Total Length of Fwd Packets",
    "FlowBytesReceived": "Total Length of Bwd Packets",
    "PacketLengthMean": "Packet Length Mean",
    "PacketLengthStandardDeviation": "Packet Length Std",
    "PacketLengthVariance": "Packet Length Variance",
    "PacketTimeMean": "Flow IAT Mean",
    "PacketTimeStandardDeviation": "Flow IAT Std",
    "PacketTimeVariance": "Flow IAT Max",
    "FlowSentRate": "Fwd Packets/s",
    "FlowReceivedRate": "Bwd Packets/s",
}

META_COLUMNS = {
    "label",
    "class",
    "traffic_type",
    "trafficcategory",
    "application",
    "source_file",
    "source_dataset",
    "original_label",
    "anomaly_label",
}


def _to_float(value: Any) -> Tuple[float, Optional[str]]:
    try:
        f = float(value)
    except Exception:
        return 0.0, "non_numeric"
    if math.isnan(f):
        return 0.0, "nan"
    if math.isinf(f):
        return (CLIP_MAX if f > 0 else CLIP_MIN), "inf"
    clipped = min(max(f, CLIP_MIN), CLIP_MAX)
    if clipped != f:
        return clipped, "clipped"
    return float(clipped), None


def label_column(columns: Iterable[str]) -> Optional[str]:
    lowered = {str(c).strip().lower(): str(c).strip() for c in columns}
    for candidate in ("label", "class", "traffic_type", "trafficcategory", "anomaly"):
        if candidate in lowered:
            return lowered[candidate]
    return None


def normalize_anomaly_label(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return "unlabeled"
    if text.lower() in {"benign", "normal", "non-doh", "nondoh"}:
        return "benign"
    if "benign" in text.lower() and "malicious" not in text.lower():
        return "benign"
    return "anomaly"


def map_dohbrw_row_to_production_features(
    row: pd.Series,
    production_features: Optional[List[str]] = None,
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    production_features = production_features or load_production_features()
    mapped_values: Dict[str, float] = {}
    source_for_feature: Dict[str, str] = {}
    sanitization: Counter[str] = Counter()

    cleaned = {str(k).strip(): v for k, v in row.items()}
    for raw_name, raw_val in cleaned.items():
        if raw_name.lower() in META_COLUMNS:
            continue
        prod_name = DIRECT_ALIASES.get(raw_name, raw_name)
        if prod_name not in production_features:
            continue
        value, reason = _to_float(raw_val)
        if reason:
            sanitization[reason] += 1
        mapped_values[prod_name] = value
        source_for_feature[prod_name] = raw_name

    sent = _to_float(cleaned.get("FlowBytesSent", 0.0))[0]
    recv = _to_float(cleaned.get("FlowBytesReceived", 0.0))[0]
    sent_rate = _to_float(cleaned.get("FlowSentRate", 0.0))[0]
    recv_rate = _to_float(cleaned.get("FlowReceivedRate", 0.0))[0]
    pkt_mean = _to_float(cleaned.get("PacketLengthMean", 0.0))[0]
    pkt_std = _to_float(cleaned.get("PacketLengthStandardDeviation", 0.0))[0]
    pkt_var = _to_float(cleaned.get("PacketLengthVariance", 0.0))[0]

    derived = {
        "Flow Bytes/s": sent_rate + recv_rate,
        "Flow Packets/s": sent_rate + recv_rate,
        "Fwd Packet Length Mean": pkt_mean,
        "Bwd Packet Length Mean": pkt_mean,
        "Fwd Packet Length Std": pkt_std,
        "Bwd Packet Length Std": pkt_std,
        "Fwd Packet Length Max": max(pkt_mean, pkt_mean + pkt_std),
        "Bwd Packet Length Max": max(pkt_mean, pkt_mean + pkt_std),
        "Fwd Packet Length Min": max(0.0, pkt_mean - pkt_std),
        "Bwd Packet Length Min": max(0.0, pkt_mean - pkt_std),
        "Min Packet Length": max(0.0, pkt_mean - pkt_std),
        "Max Packet Length": max(pkt_mean, pkt_mean + pkt_std),
        "Average Packet Size": pkt_mean,
        "Avg Fwd Segment Size": pkt_mean,
        "Avg Bwd Segment Size": pkt_mean,
        "Subflow Fwd Bytes": sent,
        "Subflow Bwd Bytes": recv,
        "Down/Up Ratio": recv / max(1.0, sent),
        "Flow IAT Min": _to_float(cleaned.get("PacketTimeMedian", 0.0))[0],
        "Flow IAT Max": max(_to_float(cleaned.get("PacketTimeVariance", 0.0))[0], pkt_var),
    }
    for prod_name, value in derived.items():
        if prod_name in production_features and prod_name not in mapped_values:
            mapped_values[prod_name] = float(value)
            source_for_feature[prod_name] = "derived:dohbrw"

    features: Dict[str, float] = {}
    missing: List[str] = []
    zero_filled: List[str] = []
    for feat in production_features:
        if feat in mapped_values:
            value, reason = _to_float(mapped_values[feat])
            if reason:
                sanitization[reason] += 1
            features[feat] = value
        else:
            features[feat] = 0.0
            missing.append(feat)
            zero_filled.append(feat)

    quality = {
        "feature_count": len(production_features),
        "mapped_count": len(source_for_feature),
        "missing_count": len(missing),
        "zero_filled_count": len(zero_filled),
        "mapped_ratio": round(len(source_for_feature) / max(1, len(production_features)), 4),
        "missing_features": missing,
        "zero_filled_features": zero_filled,
        "source_columns": source_for_feature,
        "sanitization_counts": dict(sanitization),
    }
    return features, quality


def row_dict_for_dohbrw_buffer(
    row: pd.Series,
    *,
    production_features: List[str],
    original_label: str,
    source_file: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    features, quality = map_dohbrw_row_to_production_features(row, production_features)
    anomaly_label = normalize_anomaly_label(original_label)
    rec: Dict[str, Any] = dict(features)
    rec.update(
        {
            "original_label": original_label or "unlabeled",
            "anomaly_label": anomaly_label,
            "label": anomaly_label,
            "is_anomaly": 1 if anomaly_label == "anomaly" else 0 if anomaly_label == "benign" else None,
            "source_file": source_file,
            "source_dataset": "DOHBRW",
            "source": "dataset:DOHBRW",
            "feature_mapping_quality": quality["mapped_ratio"],
            "missing_mapped_features": quality["missing_count"],
            "zero_filled_features": quality["zero_filled_count"],
        }
    )
    return rec, quality


def build_mapping_report(
    rows: Iterable[pd.Series],
    *,
    production_features: Optional[List[str]] = None,
    source_file: str = "",
    report_path: Optional[Path] = None,
) -> Dict[str, Any]:
    production_features = production_features or load_production_features()
    missing_counter: Counter[str] = Counter()
    zero_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    sanitization_counter: Counter[str] = Counter()
    ratios: List[float] = []
    row_count = 0
    for row in rows:
        _features, quality = map_dohbrw_row_to_production_features(row, production_features)
        row_count += 1
        ratios.append(float(quality.get("mapped_ratio", 0.0)))
        missing_counter.update(quality.get("missing_features") or [])
        zero_counter.update(quality.get("zero_filled_features") or [])
        source_counter.update((quality.get("source_columns") or {}).values())
        sanitization_counter.update(quality.get("sanitization_counts") or {})
    avg_ratio = float(np.mean(ratios)) if ratios else 0.0
    report = {
        "generated_at": time.time(),
        "source_file": source_file,
        "rows_analyzed": row_count,
        "production_feature_count": len(production_features),
        "avg_mapped_ratio": round(avg_ratio, 4),
        "top_missing_features": missing_counter.most_common(20),
        "top_zero_filled_features": zero_counter.most_common(20),
        "top_source_columns_used": source_counter.most_common(20),
        "sanitization_counts": dict(sanitization_counter),
        "alias_mapping": DIRECT_ALIASES,
        "status": "ok" if row_count and avg_ratio >= 0.25 else "weak_mapping",
    }
    if report_path:
        write_json(report_path, report)
    return report
