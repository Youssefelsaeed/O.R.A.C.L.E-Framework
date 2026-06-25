"""Contract validators for candidate-safe LSTM/GNN retraining buffers."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

import pandas as pd

LSTM_REQUIRED_COLUMNS = [
    "sequence_id",
    "sequence_index",
    "timestamp",
    "flow_id",
    "label",
    "is_attack",
    "attack_family",
]

GNN_REQUIRED_COLUMNS = [
    "flow_id",
    "src_ip",
    "dst_ip",
    "timestamp",
    "label",
    "is_attack",
    "attack_family",
]

META_COLUMNS = {
    "sequence_id",
    "sequence_index",
    "timestamp",
    "flow_id",
    "src_ip",
    "dst_ip",
    "label",
    "is_attack",
    "original_label",
    "attack_family",
    "source_dataset",
    "source_file",
    "source",
    "label_trust",
    "feature_mapping_quality",
    "missing_mapped_features",
    "sample_weight",
}


def _missing(df: pd.DataFrame, required: Iterable[str]) -> List[str]:
    cols = set(str(c) for c in df.columns)
    return [c for c in required if c not in cols]


def _numeric_feature_count(df: pd.DataFrame) -> int:
    count = 0
    for col in df.columns:
        if str(col) in META_COLUMNS:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        if series.notna().any():
            count += 1
    return count


def validate_lstm_buffer_contract(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate whether a DataFrame can safely feed real LSTM retraining."""
    warnings: List[str] = []
    missing_columns = _missing(df, LSTM_REQUIRED_COLUMNS)
    if df.empty:
        warnings.append("buffer_empty")

    numeric_features = _numeric_feature_count(df)
    if numeric_features < 50:
        warnings.append(f"numeric_feature_count_low:{numeric_features}")

    if "sequence_id" in df.columns:
        seq_sizes = df.groupby("sequence_id", dropna=False).size()
        if seq_sizes.empty:
            warnings.append("no_sequence_groups")
        else:
            min_len = int(seq_sizes.min())
            if min_len < 15:
                warnings.append(f"minimum_sequence_length_not_met:{min_len}<15")
    else:
        warnings.append("sequence_grouping_unavailable")

    if "sequence_index" in df.columns:
        seq_index = pd.to_numeric(df["sequence_index"], errors="coerce")
        if seq_index.isna().any():
            warnings.append("sequence_index_contains_non_numeric_values")

    if "timestamp" in df.columns:
        parsed = pd.to_datetime(df["timestamp"], errors="coerce")
        if parsed.isna().any():
            warnings.append("timestamp_contains_unparseable_values")

    if "is_attack" in df.columns:
        target = pd.to_numeric(df["is_attack"], errors="coerce")
        values = set(target.dropna().astype(int).unique().tolist())
        if not values.issubset({0, 1}):
            warnings.append("is_attack_not_binary")

    valid = not missing_columns and not any(w.startswith("minimum_sequence_length_not_met") for w in warnings)
    valid = valid and "buffer_empty" not in warnings and numeric_features >= 50
    return {
        "valid": bool(valid),
        "missing_columns": missing_columns,
        "warnings": warnings,
        "safe_to_train": bool(valid),
        "contract_name": "lstm_retraining_contract",
        "contract_version": "1.0",
    }


def validate_gnn_buffer_contract(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate whether a DataFrame can safely feed real GNN retraining."""
    warnings: List[str] = []
    missing_columns = _missing(df, GNN_REQUIRED_COLUMNS)
    if df.empty:
        warnings.append("buffer_empty")

    numeric_features = _numeric_feature_count(df)
    if numeric_features < 20:
        warnings.append(f"numeric_edge_feature_count_low:{numeric_features}")

    for col in ("src_ip", "dst_ip"):
        if col in df.columns and df[col].astype(str).str.strip().eq("").any():
            warnings.append(f"{col}_contains_empty_values")

    if "timestamp" in df.columns:
        parsed = pd.to_datetime(df["timestamp"], errors="coerce")
        if parsed.isna().any():
            warnings.append("timestamp_contains_unparseable_values")

    if "flow_id" in df.columns and df["flow_id"].astype(str).duplicated().any():
        warnings.append("duplicate_flow_id_values_present")

    if "is_attack" in df.columns:
        target = pd.to_numeric(df["is_attack"], errors="coerce")
        values = set(target.dropna().astype(int).unique().tolist())
        if not values.issubset({0, 1}):
            warnings.append("is_attack_not_binary")

    valid = not missing_columns and "buffer_empty" not in warnings and numeric_features >= 20
    valid = valid and not any(w.endswith("_contains_empty_values") for w in warnings)
    valid = valid and "timestamp_contains_unparseable_values" not in warnings
    return {
        "valid": bool(valid),
        "missing_columns": missing_columns,
        "warnings": warnings,
        "safe_to_train": bool(valid),
        "contract_name": "gnn_retraining_contract",
        "contract_version": "1.0",
    }
