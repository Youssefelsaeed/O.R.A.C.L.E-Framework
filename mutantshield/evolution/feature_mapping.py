"""CSE-CIC-IDS2018 to MutantShield production feature mapping."""
from __future__ import annotations

import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import get_config
from .candidate_trainer import _load_production_feature_schema
from .reports import write_json

CLIP_MIN = -1e6
CLIP_MAX = 1e6

CSE_TO_PRODUCTION_ALIASES: Dict[str, str] = {
    "Dst Port": "Destination Port",
    "Tot Fwd Pkts": "Total Fwd Packets",
    "Tot Bwd Pkts": "Total Backward Packets",
    "TotLen Fwd Pkts": "Total Length of Fwd Packets",
    "TotLen Bwd Pkts": "Total Length of Bwd Packets",
    "Fwd Pkt Len Max": "Fwd Packet Length Max",
    "Fwd Pkt Len Min": "Fwd Packet Length Min",
    "Fwd Pkt Len Mean": "Fwd Packet Length Mean",
    "Fwd Pkt Len Std": "Fwd Packet Length Std",
    "Bwd Pkt Len Max": "Bwd Packet Length Max",
    "Bwd Pkt Len Min": "Bwd Packet Length Min",
    "Bwd Pkt Len Mean": "Bwd Packet Length Mean",
    "Bwd Pkt Len Std": "Bwd Packet Length Std",
    "Flow Byts/s": "Flow Bytes/s",
    "Flow Pkts/s": "Flow Packets/s",
    "Fwd IAT Tot": "Fwd IAT Total",
    "Bwd IAT Tot": "Bwd IAT Total",
    "Fwd Header Len": "Fwd Header Length",
    "Bwd Header Len": "Bwd Header Length",
    "Fwd Pkts/s": "Fwd Packets/s",
    "Bwd Pkts/s": "Bwd Packets/s",
    "Pkt Len Min": "Min Packet Length",
    "Pkt Len Max": "Max Packet Length",
    "Pkt Len Mean": "Packet Length Mean",
    "Pkt Len Std": "Packet Length Std",
    "Pkt Len Var": "Packet Length Variance",
    "FIN Flag Cnt": "FIN Flag Count",
    "SYN Flag Cnt": "SYN Flag Count",
    "RST Flag Cnt": "RST Flag Count",
    "PSH Flag Cnt": "PSH Flag Count",
    "ACK Flag Cnt": "ACK Flag Count",
    "URG Flag Cnt": "URG Flag Count",
    "CWE Flag Count": "CWE Flag Count",
    "ECE Flag Cnt": "ECE Flag Count",
    "Pkt Size Avg": "Average Packet Size",
    "Fwd Seg Size Avg": "Avg Fwd Segment Size",
    "Bwd Seg Size Avg": "Avg Bwd Segment Size",
    "Fwd Byts/b Avg": "Fwd Avg Bytes/Bulk",
    "Fwd Pkts/b Avg": "Fwd Avg Packets/Bulk",
    "Fwd Blk Rate Avg": "Fwd Avg Bulk Rate",
    "Bwd Byts/b Avg": "Bwd Avg Bytes/Bulk",
    "Bwd Pkts/b Avg": "Bwd Avg Packets/Bulk",
    "Bwd Blk Rate Avg": "Bwd Avg Bulk Rate",
    "Subflow Fwd Pkts": "Subflow Fwd Packets",
    "Subflow Fwd Byts": "Subflow Fwd Bytes",
    "Subflow Bwd Pkts": "Subflow Bwd Packets",
    "Subflow Bwd Byts": "Subflow Bwd Bytes",
    "Init Fwd Win Byts": "Init_Win_bytes_forward",
    "Init Bwd Win Byts": "Init_Win_bytes_backward",
    "Fwd Act Data Pkts": "act_data_pkt_fwd",
    "Fwd Seg Size Min": "min_seg_size_forward",
}

_META_COLUMNS = {
    "label",
    "source ip",
    "destination ip",
    "src_ip",
    "dst_ip",
    "flow_id",
    "id",
    "timestamp",
}


def canonical_feature_name(name: Any) -> str:
    text = str(name).strip()
    return CSE_TO_PRODUCTION_ALIASES.get(text, text)


def load_production_features() -> List[str]:
    cfg = get_config()
    schema = _load_production_feature_schema(cfg) or []
    if schema:
        return schema
    # Conservative fallback for environments where model loading is unavailable.
    return [
        "Destination Port",
        "Flow Duration",
        "Total Fwd Packets",
        "Total Backward Packets",
        "Total Length of Fwd Packets",
        "Total Length of Bwd Packets",
        "Fwd Packet Length Max",
        "Bwd Packet Length Max",
        "Flow Bytes/s",
        "Flow Packets/s",
        "Fwd IAT Total",
        "Init_Win_bytes_forward",
        "Init_Win_bytes_backward",
        "min_seg_size_forward",
    ]


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


def map_cse_row_to_production_features(
    row: pd.Series,
    production_features: Optional[List[str]] = None,
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """Map one CSE row to exactly the production feature schema."""
    production_features = production_features or load_production_features()
    mapped_values: Dict[str, float] = {}
    source_for_feature: Dict[str, str] = {}
    sanitization: Counter[str] = Counter()

    for raw_col, raw_val in row.items():
        raw_name = str(raw_col).strip()
        if raw_name.lower() in _META_COLUMNS:
            continue
        prod_name = canonical_feature_name(raw_name)
        if prod_name not in production_features:
            continue
        value, reason = _to_float(raw_val)
        if reason:
            sanitization[reason] += 1
        mapped_values[prod_name] = value
        source_for_feature[prod_name] = raw_name

    features: Dict[str, float] = {}
    missing: List[str] = []
    zero_filled: List[str] = []
    for feat in production_features:
        if feat in mapped_values:
            features[feat] = mapped_values[feat]
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


def build_mapping_quality_report(
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
    mapped_ratios: List[float] = []
    row_count = 0

    for row in rows:
        _features, q = map_cse_row_to_production_features(row, production_features)
        row_count += 1
        mapped_ratios.append(float(q.get("mapped_ratio", 0.0)))
        missing_counter.update(q.get("missing_features") or [])
        zero_counter.update(q.get("zero_filled_features") or [])
        source_counter.update((q.get("source_columns") or {}).values())
        sanitization_counter.update(q.get("sanitization_counts") or {})

    report = {
        "generated_at": time.time(),
        "source_file": source_file,
        "rows_analyzed": row_count,
        "production_feature_count": len(production_features),
        "avg_mapped_ratio": round(float(np.mean(mapped_ratios)) if mapped_ratios else 0.0, 4),
        "top_missing_features": missing_counter.most_common(20),
        "top_zero_filled_features": zero_counter.most_common(20),
        "top_source_columns_used": source_counter.most_common(20),
        "sanitization_counts": dict(sanitization_counter),
        "alias_mapping": CSE_TO_PRODUCTION_ALIASES,
        "status": "ok" if row_count and (float(np.mean(mapped_ratios)) if mapped_ratios else 0.0) >= 0.6 else "weak_mapping",
    }
    if report_path is None:
        report_path = get_config().reports_dir / "cse_feature_mapping_report.json"
    write_json(report_path, report)
    return report


def row_dict_for_buffer(
    row: pd.Series,
    *,
    production_features: List[str],
    original_label: str,
    source_file: str,
    source_dataset: str = "CSE-CIC-IDS2018",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    features, quality = map_cse_row_to_production_features(row, production_features)
    is_attack = 0 if str(original_label).strip().upper() == "BENIGN" else 1
    rec: Dict[str, Any] = dict(features)
    rec.update(
        {
            "original_label": original_label,
            "label": "attack" if is_attack else "benign",
            "is_attack": is_attack,
            "source_file": source_file,
            "source_dataset": source_dataset,
            "source": f"dataset:{source_dataset}",
            "label_trust": "verified_dataset",
            "feature_mapping_quality": quality["mapped_ratio"],
            "missing_mapped_features": quality["missing_count"],
        }
    )
    return rec, quality
