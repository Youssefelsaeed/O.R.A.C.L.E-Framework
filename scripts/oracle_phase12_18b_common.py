"""Shared helpers for Phase 12.18B controlled detection verification."""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "final"
EVAL_SET_DIR = REPORT_DIR / "phase12_18b_eval_sets"
CORE = "http://127.0.0.1:8000"
GUI = "http://127.0.0.1:4173"
SEED = 1218

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATASETS: Dict[str, Dict[str, Any]] = {
    "CIC-IDS2017": {
        "paths": [ROOT / "Workin with" / "CIC-17", ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "Data set" / "CIC-2017 (baseline)"],
        "domain": "cic",
        "label_hints": ["Label", "label", " Label"],
        "eval_file": "cic_ids2017_balanced.csv",
    },
    "UNSW-NB15": {
        "paths": [ROOT / "Workin with" / "UNSWB15", ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "Data set" / "UNWB-2015"],
        "domain": "unsw",
        "label_hints": ["label", "Label", "attack_cat", "class"],
        "eval_file": "unsw_nb15_balanced.csv",
    },
    "CSE-CIC-IDS2018": {
        "paths": [ROOT / "Workin with" / "CSE-CIC-IDS-2018"],
        "domain": "cse",
        "label_hints": ["Label", "label"],
        "eval_file": "cse_cic_ids2018_balanced.csv",
    },
    "DoHBrw": {
        "paths": [ROOT / "Workin with" / "DohbrW"],
        "domain": "dohbrw",
        "label_hints": ["Label", "label", "class", "traffic_type", "trafficCategory", "anomaly", "is_anomaly"],
        "eval_file": "dohbrw_balanced.csv",
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
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL, timeout=5).strip()
    except Exception:
        return None


def import_pandas():
    import pandas as pd  # type: ignore

    return pd


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


def detect_label_column(columns: Iterable[str], hints: Iterable[str]) -> Optional[str]:
    lowered = {str(c).strip().lower(): str(c) for c in columns}
    for hint in hints:
        key = str(hint).strip().lower()
        if key in lowered:
            return lowered[key]
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
    if "benign" in text and "malicious" not in text:
        return 0
    if text in {"1", "true", "yes", "attack", "anomaly", "malicious"}:
        return 1
    return 1


def attack_family(value: Any, y_true: int) -> str:
    text = str(value).strip()
    if not text or text.lower() in {"0", "1"}:
        return "benign" if y_true == 0 else "attack"
    return text


def read_csv_preview(path: Path, rows: int):
    pd = import_pandas()
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path).head(rows)
    return pd.read_csv(path, low_memory=False, nrows=rows)


def collect_balanced_rows(dataset_name: str, target_per_class: int = 500, chunk_size: int = 20000):
    pd = import_pandas()
    files = discover_dataset_files(dataset_name)
    benign_parts: List[Any] = []
    attack_parts: List[Any] = []
    inspected: List[Dict[str, Any]] = []
    for path in files:
        try:
            preview = read_csv_preview(path, 200)
            label_col = detect_label_column(preview.columns, DATASETS[dataset_name]["label_hints"])
            if not label_col:
                inspected.append({"file": str(path), "status": "label_missing"})
                continue
            iterator = [pd.read_parquet(path)] if path.suffix.lower() == ".parquet" else pd.read_csv(path, low_memory=False, chunksize=chunk_size)
            for chunk in iterator:
                if label_col not in chunk.columns:
                    continue
                chunk = chunk.copy()
                chunk["original_label"] = chunk[label_col].astype(str)
                chunk["y_true"] = chunk[label_col].map(normalize_binary_label).astype(int)
                chunk["dataset_source"] = dataset_name
                chunk["attack_family"] = [attack_family(v, y) for v, y in zip(chunk[label_col], chunk["y_true"])]
                chunk["row_origin_file"] = str(path)
                benign = chunk[chunk["y_true"] == 0]
                attack = chunk[chunk["y_true"] == 1]
                if len(benign) and sum(len(x) for x in benign_parts) < target_per_class:
                    benign_parts.append(benign.head(target_per_class))
                if len(attack) and sum(len(x) for x in attack_parts) < target_per_class:
                    attack_parts.append(attack.head(target_per_class))
                if sum(len(x) for x in benign_parts) >= target_per_class and sum(len(x) for x in attack_parts) >= target_per_class:
                    break
            inspected.append({"file": str(path), "status": "used", "label_column": label_col})
        except Exception as exc:
            inspected.append({"file": str(path), "status": "error", "error": f"{type(exc).__name__}:{exc}"})
        if sum(len(x) for x in benign_parts) >= target_per_class and sum(len(x) for x in attack_parts) >= target_per_class:
            break
    benign_df = pd.concat(benign_parts, ignore_index=True) if benign_parts else pd.DataFrame()
    attack_df = pd.concat(attack_parts, ignore_index=True) if attack_parts else pd.DataFrame()
    if len(benign_df) > target_per_class:
        benign_df = benign_df.sample(n=target_per_class, random_state=SEED)
    if len(attack_df) > target_per_class:
        attack_df = attack_df.sample(n=target_per_class, random_state=SEED)
    combined = pd.concat([benign_df, attack_df], ignore_index=True) if len(benign_df) or len(attack_df) else pd.DataFrame()
    if len(combined):
        combined = combined.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    return combined, inspected


def load_eval_set(dataset_name: str):
    pd = import_pandas()
    path = EVAL_SET_DIR / DATASETS[dataset_name]["eval_file"]
    return pd.read_csv(path, low_memory=False)


def load_production_features() -> List[str]:
    from mutantshield.evolution.feature_mapping import load_production_features as _load

    return _load()


def map_row_to_features(row: Any, dataset_name: str, production_features: List[str]) -> Tuple[Dict[str, float], Dict[str, Any]]:
    domain = DATASETS[dataset_name]["domain"]
    if domain in {"cic", "cse", "dohbrw"}:
        from mutantshield.evolution.feature_mapping import map_cse_row_to_production_features

        return map_cse_row_to_production_features(row, production_features)
    if domain == "unsw":
        from mutantshield.evolution.unsw_mapping import mapping_quality, unsw_row_to_cic_features

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
    return {f: 0.0 for f in production_features}, {"mapped_ratio": 0.0, "mapped_count": 0, "feature_count": len(production_features)}


def predict_production(features: Dict[str, float]) -> Tuple[Dict[str, Any], Dict[str, Any], bool]:
    from oracle_sensor.mutantshield_client import predict_decision

    started = time.perf_counter()
    decision, raw = predict_decision(features)
    raw = dict(raw or {})
    raw["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 4)
    fallback = str(raw.get("source", "")).lower() == "fallback_heuristic" or str(decision.get("model_consensus", "")).lower() == "fallback"
    return decision, raw, fallback


def predict_candidate(features: Dict[str, float], candidate_id: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any], bool]:
    try:
        from mutantshield.evolution.candidate_inference import load_candidate

        candidate_root = ROOT / "models_candidate"
        if not candidate_id:
            candidates = [p.name for p in candidate_root.iterdir() if p.is_dir()] if candidate_root.exists() else []
            candidate_id = sorted(candidates)[-1] if candidates else ""
        if not candidate_id:
            return None, {"error": "candidate_unavailable"}, True
        started = time.perf_counter()
        engine = load_candidate(candidate_id)
        decision, raw = engine.predict(features)
        raw["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 4)
        return decision, raw, False
    except Exception as exc:
        return None, {"error": f"{type(exc).__name__}:{exc}"}, True


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
        return None, {"error": f"{type(exc).__name__}:{exc}"}, True


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return round(float(ordered[max(0, min(idx, len(ordered) - 1))]), 4)


def binary_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, Any]:
    positives = sum(1 for y in y_true if y == 1)
    negatives = sum(1 for y in y_true if y == 0)
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    limited = positives == 0 or negatives == 0
    return {
        "limited": limited,
        "positive_count": positives,
        "negative_count": negatives,
        "accuracy": None if limited else round((tp + tn) / max(1, len(y_true)), 4),
        "precision": None if limited else round(precision, 4),
        "recall": None if limited else round(recall, 4),
        "f1": None if limited else round(f1, 4),
        "false_positive_rate": None if negatives == 0 else round(fp / max(1, fp + tn), 4),
        "false_negative_rate": None if positives == 0 else round(fn / max(1, fn + tp), 4),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def per_attack_family_recall(families: List[str], y_true: List[int], y_pred: List[int]) -> Dict[str, Any]:
    stats: Dict[str, Counter[str]] = defaultdict(Counter)
    for fam, true, pred in zip(families, y_true, y_pred):
        if true == 1:
            stats[str(fam)]["attack_rows"] += 1
            if pred == 1:
                stats[str(fam)]["detected"] += 1
    return {
        fam: {
            "attack_rows": int(c["attack_rows"]),
            "detected": int(c["detected"]),
            "recall": round(c["detected"] / max(1, c["attack_rows"]), 4),
        }
        for fam, c in sorted(stats.items())
    }


def score_summary(scores: List[float]) -> Dict[str, Any]:
    if not scores:
        return {"count": 0}
    return {"count": len(scores), "avg": round(sum(scores) / len(scores), 4), "p50": percentile(scores, 50), "p95": percentile(scores, 95), "min": round(min(scores), 4), "max": round(max(scores), 4)}

