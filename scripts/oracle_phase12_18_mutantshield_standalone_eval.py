"""Phase 12.18 MutantShield standalone per-dataset evaluation."""
from __future__ import annotations

import time
from collections import Counter
from typing import Any, Dict, List

from oracle_phase12_18_common import (
    DATASETS,
    binary_metrics,
    compact_error,
    discover_dataset_files,
    load_production_features,
    map_row_to_features,
    normalize_binary_label,
    per_family_recall,
    predict_dohbrw_native,
    predict_mutantshield,
    read_labeled_dataset_sample,
    summarize_scores,
    write_json,
    write_md,
)


EVAL_TARGETS = [
    ("CIC-IDS2017", "mapped_cic"),
    ("UNSW-NB15", "mapped_cic"),
    ("CSE-CIC-IDS2018", "mapped_cic"),
    ("DoHBrw", "mapped_cic"),
    ("DoHBrw", "native_adapter"),
]


def _eval_target(dataset_name: str, path_name: str, sample_size: int) -> Dict[str, Any]:
    files = discover_dataset_files(dataset_name)
    if not files:
        return {
            "dataset": dataset_name,
            "path": path_name,
            "status": "BLOCKED_MISSING_DATASET",
            "rows_tested": 0,
            "note": "Dataset files are absent; no detection metrics were fabricated.",
        }
    try:
        source_file, df, label_col, files = read_labeled_dataset_sample(dataset_name, sample_size=sample_size)
        if not label_col:
            return {"dataset": dataset_name, "path": path_name, "status": "BLOCKED_LABEL_COLUMN_MISSING", "source_file": str(source_file)}
        production_features = load_production_features()
        y_true: List[int] = []
        y_pred: List[int] = []
        labels: List[str] = []
        scores: List[float] = []
        latencies: List[float] = []
        risk_labels: Counter[str] = Counter()
        consensus: Counter[str] = Counter()
        fallbacks = 0
        samples: List[Dict[str, Any]] = []
        started = time.perf_counter()
        for idx, row in df.iterrows():
            true = normalize_binary_label(row[label_col])
            label_text = str(row[label_col])
            if path_name == "native_adapter":
                decision, raw, fallback = predict_dohbrw_native(row)
                if decision is None:
                    return {
                        "dataset": dataset_name,
                        "path": path_name,
                        "status": "BLOCKED_ADAPTER_UNAVAILABLE",
                        "source_file": str(source_file),
                        "error": raw.get("error"),
                    }
            else:
                features, quality = map_row_to_features(row, dataset_name, production_features)
                decision, raw, fallback = predict_mutantshield(features)
                raw["feature_quality"] = quality
            pred = 1 if bool(decision.get("is_attack")) else 0
            score = float(decision.get("risk_score", 0.0))
            y_true.append(true)
            y_pred.append(pred)
            labels.append(label_text)
            scores.append(score)
            latencies.append(float(raw.get("latency_ms", 0.0) or 0.0))
            risk_labels[str(decision.get("risk_label"))] += 1
            consensus[str(decision.get("model_consensus"))] += 1
            fallbacks += 1 if fallback else 0
            if len(samples) < 10:
                samples.append(
                    {
                        "row_index": int(idx) if isinstance(idx, int) else str(idx),
                        "label": label_text,
                        "risk_score": score,
                        "risk_label": decision.get("risk_label"),
                        "is_attack": decision.get("is_attack"),
                        "model_consensus": decision.get("model_consensus"),
                        "fallback": fallback,
                    }
                )
        metrics = binary_metrics(y_true, y_pred)
        metrics["per_attack_family_recall"] = per_family_recall(labels, y_true, y_pred)
        duration = time.perf_counter() - started
        return {
            "dataset": dataset_name,
            "path": path_name,
            "status": "PASS" if y_true else "NO_ROWS",
            "source_file": str(source_file),
            "rows_tested": len(y_true),
            "fallback_path_used": fallbacks > 0,
            "fallback_count": fallbacks,
            "model_consensus_distribution": dict(consensus),
            "risk_score_distribution": summarize_scores(scores),
            "risk_label_distribution": dict(risk_labels),
            "metrics": metrics,
            "avg_inference_latency_ms": round(sum(latencies) / max(1, len(latencies)), 4),
            "p95_inference_latency_ms": sorted(latencies)[int(0.95 * (len(latencies) - 1))] if latencies else 0.0,
            "throughput_samples_sec": round(len(y_true) / max(0.001, duration), 2),
            "sample_records": samples,
        }
    except Exception as exc:
        return {"dataset": dataset_name, "path": path_name, "status": "ERROR", "source_file": str(files[0]) if files else "", "error": compact_error(exc)}


def run(sample_size: int = 50) -> Dict[str, Any]:
    results = {f"{dataset}:{path}": _eval_target(dataset, path, sample_size) for dataset, path in EVAL_TARGETS}
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "sample_size": sample_size,
        "results": results,
        "pass": all(item["status"] in {"PASS", "BLOCKED_MISSING_DATASET", "BLOCKED_ADAPTER_UNAVAILABLE", "BLOCKED_LABEL_COLUMN_MISSING"} for item in results.values()),
        "truth_policy": "Metrics are computed only from available labeled rows using real inference; blocked datasets are not assigned substitute metrics.",
    }
    json_path = write_json("phase12_18_mutantshield_standalone_eval.json", report)
    md = ["# MutantShield Standalone Dataset Evaluation", ""]
    for key, item in results.items():
        m = item.get("metrics") or {}
        md += [
            f"## {key}",
            f"- Status: `{item.get('status')}`",
            f"- Rows tested: `{item.get('rows_tested')}`",
            f"- Fallback used: `{item.get('fallback_path_used')}`",
            f"- Accuracy/Precision/Recall/F1: `{m.get('accuracy')}` / `{m.get('precision')}` / `{m.get('recall')}` / `{m.get('f1')}`",
            f"- FPR/FNR: `{m.get('false_positive_rate')}` / `{m.get('false_negative_rate')}`",
            f"- Note/Error: {item.get('note') or item.get('error') or ''}",
            "",
        ]
    md_path = write_md("phase12_18_mutantshield_standalone_eval.md", md)
    report["json_report_path"] = str(json_path)
    report["markdown_report_path"] = str(md_path)
    return report


def main() -> None:
    report = run()
    print("\n=== MUTANTSHIELD STANDALONE DATASET EVALUATION ===")
    labels = {
        "CIC-IDS2017:mapped_cic": "CIC-IDS2017",
        "UNSW-NB15:mapped_cic": "UNSW-NB15",
        "CSE-CIC-IDS2018:mapped_cic": "CSE-CIC-IDS2018",
        "DoHBrw:mapped_cic": "DoHBrw Mapped Path",
        "DoHBrw:native_adapter": "DoHBrw Native Adapter",
    }
    for key, label in labels.items():
        item = report["results"].get(key, {})
        metrics = item.get("metrics") or {}
        print(f"{label}: {item.get('status')} accuracy={metrics.get('accuracy')} recall={metrics.get('recall')} f1={metrics.get('f1')}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['json_report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
