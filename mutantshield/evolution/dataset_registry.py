"""Official dataset registry for Evolution Engine."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import EvolutionConfig
from .reports import read_json, write_json

KNOWN_DATASETS = {
    "CIC-IDS2017": {
        "purpose": "baseline_training",
        "label_column": "Label",
    },
    "UNSW-NB15": {
        "purpose": "cross_validation",
        "label_column": "label",
    },
    "CSE-CIC-IDS2018": {
        "purpose": "stress_testing",
        "label_column": "Label",
    },
    "CIC-DoHBrw-2020": {
        "purpose": "anomaly_encrypted_testing",
        "label_column": "Label",
    },
}


def fingerprint_dataset(path: Path, sample_bytes: int = 65536) -> str:
    h = hashlib.sha256()
    if path.is_dir():
        files = sorted(path.glob("*.csv"))[:5]
        for f in files:
            h.update(f.name.encode())
            with f.open("rb") as fh:
                h.update(fh.read(sample_bytes))
    elif path.exists():
        with path.open("rb") as fh:
            h.update(fh.read(sample_bytes))
    else:
        h.update(str(path).encode())
    return h.hexdigest()


def validate_schema(df: pd.DataFrame, label_column: str) -> Dict[str, Any]:
    numeric_cols = [c for c in df.columns if c != label_column and pd.api.types.is_numeric_dtype(df[c])]
    return {
        "valid": label_column in df.columns and len(numeric_cols) > 0,
        "row_count": len(df),
        "feature_columns": numeric_cols[:200],
        "label_column": label_column,
        "missing_label_rows": int(df[label_column].isna().sum()) if label_column in df.columns else len(df),
    }


def register_dataset(
    cfg: EvolutionConfig,
    name: str,
    path: Path,
    label_column: Optional[str] = None,
) -> Dict[str, Any]:
    meta = KNOWN_DATASETS.get(name, {"purpose": "custom", "label_column": label_column or "Label"})
    label_col = label_column or meta["label_column"]
    entry = {
        "dataset_name": name,
        "dataset_path": str(path),
        "label_column": label_col,
        "fingerprint_sha256": fingerprint_dataset(path),
        "created_at": time.time(),
        "purpose": meta.get("purpose", "custom"),
        "row_count": 0,
        "feature_columns": [],
    }
    if path.is_dir():
        files = list(path.glob("*.csv"))
        if files:
            sample = load_dataset_sample(name, path, label_col, max_rows=500)
            if sample is not None:
                schema = validate_schema(sample, label_col)
                entry["row_count"] = schema["row_count"]
                entry["feature_columns"] = schema["feature_columns"]
    elif path.exists():
        sample = load_dataset_sample(name, path, label_col, max_rows=500)
        if sample is not None:
            schema = validate_schema(sample, label_col)
            entry["row_count"] = schema["row_count"]
            entry["feature_columns"] = schema["feature_columns"]
    registry = read_json(cfg.dataset_registry_path)
    datasets: List[Dict[str, Any]] = registry.get("datasets", [])
    datasets = [d for d in datasets if d.get("dataset_name") != name]
    datasets.append(entry)
    write_json(cfg.dataset_registry_path, {"datasets": datasets, "updated_at": time.time()})
    return entry


def load_dataset_sample(
    name: str,
    path: Path,
    label_column: str,
    max_rows: int = 5000,
) -> Optional[pd.DataFrame]:
    try:
        if path.is_dir():
            files = sorted(path.glob("*.csv"))
            if not files:
                return None
            frames = []
            remaining = max_rows
            for f in files:
                if remaining <= 0:
                    break
                chunk = pd.read_csv(f, nrows=remaining, low_memory=False)
                frames.append(chunk)
                remaining -= len(chunk)
            return pd.concat(frames, ignore_index=True) if frames else None
        return pd.read_csv(path, nrows=max_rows, low_memory=False)
    except Exception:
        return None


def bootstrap_default_datasets(cfg: EvolutionConfig) -> List[Dict[str, Any]]:
    registered: List[Dict[str, Any]] = []
    if cfg.default_cic_path.exists():
        registered.append(register_dataset(cfg, "CIC-IDS2017", cfg.default_cic_path))
    if cfg.default_unsw_path.exists():
        registered.append(register_dataset(cfg, "UNSW-NB15", cfg.default_unsw_path))
    return registered


def list_datasets(cfg: EvolutionConfig) -> List[Dict[str, Any]]:
    return read_json(cfg.dataset_registry_path).get("datasets", [])
