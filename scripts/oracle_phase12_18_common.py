"""Shared helpers for Phase 12.18 detection truth audit."""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "final"
CORE = "http://127.0.0.1:8000"
GUI = "http://127.0.0.1:4173"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DATASETS: Dict[str, Dict[str, Any]] = {
    "CIC-IDS2017": {
        "paths": [ROOT / "Workin with" / "CIC-17", ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "Data set" / "CIC-2017 (baseline)"],
        "domain": "cic",
        "label_hint": ["Label", "label", "Attack", "Class"],
    },
    "UNSW-NB15": {
        "paths": [ROOT / "Workin with" / "UNSWB15", ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "Data set" / "UNWB-2015"],
        "domain": "unsw",
        "label_hint": ["label", "Label", "attack_cat", "class"],
    },
    "CSE-CIC-IDS2018": {
        "paths": [ROOT / "Workin with" / "CSE-CIC-IDS-2018"],
        "domain": "cse",
        "label_hint": ["Label", "label"],
    },
    "DoHBrw": {
        "paths": [ROOT / "Workin with" / "DohbrW"],
        "domain": "dohbrw",
        "label_hint": ["Label", "label", "class", "traffic_type", "trafficCategory", "anomaly", "is_anomaly"],
    },
}


def write_json(name: str, report: Dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / name
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def write_md(name: str, lines: Iterable[str]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def git_commit() -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return None


def discover_dataset_files(dataset_name: str) -> List[Path]:
    spec = DATASETS[dataset_name]
    files: List[Path] = []
    for base in spec["paths"]:
        if base.is_file() and base.suffix.lower() in {".csv", ".parquet"}:
            files.append(base)
        elif base.exists():
            files.extend(list(base.rglob("*.csv")))
            files.extend(list(base.rglob("*.parquet")))
    return sorted({p.resolve() for p in files}, key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)


def import_pandas():
    try:
        import pandas as pd  # type: ignore

        return pd, None
    except Exception as exc:
        return None, str(exc)


def read_sample(path: Path, sample_size: int = 1000):
    pd, err = import_pandas()
    if pd is None:
        raise RuntimeError(f"pandas_unavailable:{err}")
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, low_memory=False, nrows=max(sample_size * 5, sample_size))
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=1218)
    return df


def read_labeled_dataset_sample(dataset_name: str, sample_size: int = 1000):
    files = discover_dataset_files(dataset_name)
    last_error = None
    for path in files:
        try:
            df = read_sample(path, sample_size=sample_size)
            label_col = detect_label_column(df.columns, DATASETS[dataset_name].get("label_hint") or [])
            if label_col:
                return path, df, label_col, files
        except Exception as exc:
            last_error = exc
            continue
    if files:
        path = files[0]
        df = read_sample(path, sample_size=sample_size)
        return path, df, detect_label_column(df.columns, DATASETS[dataset_name].get("label_hint") or []), files
    if last_error:
        raise last_error
    raise FileNotFoundError(f"dataset_files_missing:{dataset_name}")


def detect_label_column(columns: Iterable[str], hints: Iterable[str] = ()) -> Optional[str]:
    cols = [str(c) for c in columns]
    lowered = {c.lower().strip(): c for c in cols}
    for hint in hints:
        if hint.lower().strip() in lowered:
            return lowered[hint.lower().strip()]
    for candidate in ("label", "class", "attack_cat", "traffic_type", "trafficcategory", "anomaly", "is_anomaly"):
        if candidate in lowered:
            return lowered[candidate]
    return None


def normalize_binary_label(value: Any) -> int:
    text = str(value).strip().lower()
    if text in {"0", "benign", "normal", "non-doh", "nondoh", "false", "no"}:
        return 0
    if text in {"", "nan", "none", "unlabeled"}:
        return 0
    return 1


def numeric_columns(df: Any, label_col: Optional[str]) -> List[str]:
    cols: List[str] = []
    for col in df.columns:
        if label_col and str(col) == label_col:
            continue
        try:
            converted = df[col].astype("float64")
            if converted.notna().any():
                cols.append(str(col))
        except Exception:
            continue
    return cols


def risk_label(score: float) -> str:
    if score >= 0.85:
        return "CRITICAL"
    if score >= 0.65:
        return "HIGH"
    if score >= 0.35:
        return "MEDIUM"
    return "LOW"


def confidence(score: float) -> str:
    dist = abs(score - 0.5)
    if dist >= 0.35:
        return "HIGH"
    if dist >= 0.2:
        return "MEDIUM"
    return "LOW"


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return round(float(ordered[max(0, min(idx, len(ordered) - 1))]), 4)


def binary_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, Any]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    total = max(1, tp + tn + fp + fn)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "accuracy": round((tp + tn) / total, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fp / max(1, fp + tn), 4),
        "false_negative_rate": round(fn / max(1, fn + tp), 4),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def summarize_scores(scores: List[float]) -> Dict[str, Any]:
    if not scores:
        return {"count": 0}
    return {
        "count": len(scores),
        "avg": round(sum(scores) / len(scores), 4),
        "p50": percentile(scores, 50),
        "p95": percentile(scores, 95),
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
    }


def load_production_features() -> List[str]:
    from mutantshield.evolution.feature_mapping import load_production_features as _load

    return _load()


def map_row_to_features(row: Any, dataset_name: str, production_features: List[str]) -> Tuple[Dict[str, float], Dict[str, Any]]:
    domain = DATASETS[dataset_name]["domain"]
    if domain in {"cic", "cse"}:
        from mutantshield.evolution.feature_mapping import map_cse_row_to_production_features

        return map_cse_row_to_production_features(row, production_features)
    if domain == "unsw":
        from mutantshield.evolution.unsw_mapping import unsw_row_to_cic_features, mapping_quality

        features = unsw_row_to_cic_features(row, production_features)
        quality, mapped, zero = mapping_quality(production_features)
        return features, {
            "feature_count": len(production_features),
            "mapped_count": mapped,
            "missing_count": zero,
            "zero_filled_count": zero,
            "mapped_ratio": round(mapped / max(1, len(production_features)), 4),
            "quality_label": quality,
            "missing_features": [f for f in production_features if f not in features or features.get(f) == 0.0],
        }
    if domain == "dohbrw":
        from mutantshield.evolution.feature_mapping import map_cse_row_to_production_features

        return map_cse_row_to_production_features(row, production_features)
    return ({feat: 0.0 for feat in production_features}, {"mapped_ratio": 0.0, "mapped_count": 0, "feature_count": len(production_features)})


def predict_mutantshield(features: Dict[str, float]) -> Tuple[Dict[str, Any], Dict[str, Any], bool]:
    from oracle_sensor.mutantshield_client import predict_decision

    started = time.perf_counter()
    decision, raw = predict_decision(features)
    raw = dict(raw or {})
    raw["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 4)
    fallback = str(raw.get("source", "")).lower() == "fallback_heuristic" or str(decision.get("model_consensus", "")).lower() == "fallback"
    return decision, raw, fallback


def predict_dohbrw_native(row: Any) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any], bool]:
    try:
        from mutantshield.evolution.dohbrw_candidate_inference import load_dohbrw_candidate
        from mutantshield.evolution.reports import read_json

        training = read_json(ROOT / "reports" / "evolution" / "dohbrw_anomaly_adapter_training_report.json")
        candidate_id = str(training.get("candidate_id") or "")
        if not candidate_id:
            return None, {"error": "dohbrw_candidate_id_missing"}, True
        started = time.perf_counter()
        adapter = load_dohbrw_candidate(candidate_id)
        decision, raw = adapter.predict(row)
        raw = dict(raw or {})
        raw["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 4)
        return decision, raw, False
    except Exception as exc:
        return None, {"error": str(exc)}, True


def per_family_recall(labels: List[str], y_true: List[int], y_pred: List[int]) -> Dict[str, Any]:
    stats: Dict[str, Counter[str]] = defaultdict(Counter)
    for label, true, pred in zip(labels, y_true, y_pred):
        if true == 1:
            stats[str(label)]["attack_rows"] += 1
            if pred == 1:
                stats[str(label)]["detected"] += 1
    return {
        label: {
            "attack_rows": int(c["attack_rows"]),
            "detected": int(c["detected"]),
            "recall": round(c["detected"] / max(1, c["attack_rows"]), 4),
        }
        for label, c in sorted(stats.items())
    }


def compact_error(exc: Exception) -> str:
    return f"{type(exc).__name__}:{exc}"
