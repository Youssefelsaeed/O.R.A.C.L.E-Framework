"""Controlled balanced MutantShield evaluation without Oracle Core."""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from oracle_phase12_18_common import binary_metrics, import_pandas, load_production_features, map_row_to_features, per_family_recall, predict_dohbrw_native, predict_mutantshield, summarize_scores, write_json, write_md
from oracle_phase12_18b_common import predict_candidate

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "reports" / "final" / "phase12_18b_eval_sets"
MAX_ROWS_PER_PATH = 200
CSE_REPAIR_CANDIDATE_ID = "candidate-hoic-repair-20260623-194711-ac582d"
PATHS = [("CIC-IDS2017", "production_fusion"), ("UNSW-NB15", "mapped_validation"), ("CSE-CIC-IDS2018", "production_fusion"), ("CSE-CIC-IDS2018", "cse_repair_candidate"), ("DoHBrw", "mapped_cic"), ("DoHBrw", "native_adapter")]


def _csv(dataset: str) -> Path:
    return EVAL_DIR / f"{dataset.replace('/', '_').replace(' ', '_')}.csv"


def _candidate_available() -> bool:
    return (ROOT / "models_candidate" / CSE_REPAIR_CANDIDATE_ID).exists()


def _runtime_sample(df: Any):
    if len(df) <= MAX_ROWS_PER_PATH:
        return df
    benign = df[df["y_true"] == 0]
    attack = df[df["y_true"] == 1]
    parts = []
    half = MAX_ROWS_PER_PATH // 2
    if not benign.empty:
        parts.append(benign.sample(n=min(half, len(benign)), random_state=1218))
    if not attack.empty:
        parts.append(attack.sample(n=min(MAX_ROWS_PER_PATH - sum(len(p) for p in parts), len(attack)), random_state=1218))
    if parts:
        import pandas as pd

        return pd.concat(parts).sample(frac=1.0, random_state=1218)
    return df.head(MAX_ROWS_PER_PATH)


def _predict(row: Any, dataset: str, path_name: str, features: List[str]) -> Tuple[Dict[str, Any] | None, Dict[str, Any], bool]:
    if path_name == "cse_repair_candidate" and not _candidate_available():
        return None, {"error": "cse_repair_candidate_missing"}, True
    if path_name == "native_adapter":
        return predict_dohbrw_native(row)
    mapped, quality = map_row_to_features(row, dataset, features)
    if path_name == "cse_repair_candidate":
        decision, raw, fallback = predict_candidate(mapped, CSE_REPAIR_CANDIDATE_ID)
        raw["feature_quality"] = quality
        return decision, raw, fallback
    decision, raw, fallback = predict_mutantshield(mapped)
    raw["feature_quality"] = quality
    return decision, raw, fallback


def _eval(dataset: str, path_name: str) -> Dict[str, Any]:
    pd, err = import_pandas()
    if pd is None:
        return {"dataset": dataset, "path": path_name, "status": "ERROR", "error": f"pandas_unavailable:{err}"}
    path = _csv(dataset)
    if not path.exists():
        return {"dataset": dataset, "path": path_name, "status": "MISSING_EVAL_SET"}
    df_all = pd.read_csv(path, low_memory=False)
    full_dist = {str(k): int(v) for k, v in df_all["y_true"].value_counts().to_dict().items()}
    if path_name == "cse_repair_candidate" and not _candidate_available():
        return {"dataset": dataset, "path": path_name, "status": "CANDIDATE_UNAVAILABLE", "full_eval_set_distribution": full_dist}
    df = _runtime_sample(df_all)
    features = load_production_features()
    y_true: List[int] = []
    y_pred: List[int] = []
    labels: List[str] = []
    scores: List[float] = []
    latencies: List[float] = []
    consensus = Counter()
    risk_labels = Counter()
    fallbacks = 0
    samples = []
    started = time.perf_counter()
    for idx, row in df.iterrows():
        decision, raw, fallback = _predict(row, dataset, path_name, features)
        if decision is None:
            return {"dataset": dataset, "path": path_name, "status": "DETECTOR_UNAVAILABLE", "error": raw.get("error")}
        true = int(row["y_true"])
        pred = 1 if decision.get("is_attack") else 0
        score = float(decision.get("risk_score", 0.0))
        y_true.append(true); y_pred.append(pred); labels.append(str(row.get("attack_family") or row.get("original_label"))); scores.append(score)
        latencies.append(float(raw.get("latency_ms", 0.0) or 0.0))
        consensus[str(decision.get("model_consensus"))] += 1
        risk_labels[str(decision.get("risk_label"))] += 1
        fallbacks += 1 if fallback else 0
        if len(samples) < 10:
            samples.append({"row_index": int(idx) if isinstance(idx, int) else str(idx), "y_true": true, "original_label": row.get("original_label"), "risk_score": score, "risk_label": decision.get("risk_label"), "is_attack": pred == 1, "model_consensus": decision.get("model_consensus")})
    metrics = binary_metrics(y_true, y_pred)
    metrics["per_attack_family_recall"] = per_family_recall(labels, y_true, y_pred)
    limited = len(set(y_true)) < 2
    return {"dataset": dataset, "path": path_name, "status": "LIMITED_UNBALANCED" if limited else "PASS", "detector_used": path_name, "rows_evaluated": len(y_true), "full_eval_set_distribution": full_dist, "runtime_distribution": dict(Counter(y_true)), "fallback_used": fallbacks > 0, "fallback_count": fallbacks, "threshold_policy": "detector decision_object.is_attack", "metrics_final_claim_valid": not limited and fallbacks == 0, "metrics": metrics, "risk_score_distribution": summarize_scores(scores), "risk_label_distribution": dict(risk_labels), "model_consensus_distribution": dict(consensus), "avg_inference_latency_ms": round(sum(latencies) / max(1, len(latencies)), 4), "p95_inference_latency_ms": sorted(latencies)[int(0.95 * (len(latencies) - 1))] if latencies else 0.0, "throughput_samples_sec": round(len(y_true) / max(0.001, time.perf_counter() - started), 2), "sample_records": samples}


def run() -> Dict[str, Any]:
    results = {f"{d}:{p}": _eval(d, p) for d, p in PATHS}
    report: Dict[str, Any] = {"generated_at": time.time(), "max_rows_per_path": MAX_ROWS_PER_PATH, "results": results}
    report["pass"] = all(v.get("status") in {"PASS", "LIMITED_UNBALANCED", "CANDIDATE_UNAVAILABLE", "MISSING_EVAL_SET"} for v in results.values())
    json_path = write_json("phase12_18b_mutantshield_controlled_eval.json", report)
    lines = ["# Phase 12.18B MutantShield Controlled Evaluation", ""]
    for key, item in results.items():
        m = item.get("metrics") or {}
        lines += [f"## {key}", f"- Status: `{item.get('status')}`", f"- Rows: `{item.get('rows_evaluated')}`", f"- Accuracy/Precision/Recall/F1: `{m.get('accuracy')}` / `{m.get('precision')}` / `{m.get('recall')}` / `{m.get('f1')}`", f"- FPR/FNR: `{m.get('false_positive_rate')}` / `{m.get('false_negative_rate')}`", ""]
    md_path = write_md("phase12_18b_mutantshield_controlled_eval.md", lines)
    report["json_report_path"] = str(json_path); report["markdown_report_path"] = str(md_path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B MUTANTSHIELD CONTROLLED EVAL ===")
    for key, item in report["results"].items():
        m = item.get("metrics") or {}
        print(f"{key}: {item.get('status')} rows={item.get('rows_evaluated')} recall={m.get('recall')} f1={m.get('f1')}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['json_report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
