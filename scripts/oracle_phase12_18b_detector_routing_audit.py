"""Audit detector routing for Phase 12.18B balanced eval sets."""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict

from oracle_phase12_18_common import DATASETS, import_pandas, load_production_features, map_row_to_features, write_json

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "reports" / "final" / "phase12_18b_eval_sets"


def _csv(dataset: str) -> Path:
    return EVAL_DIR / f"{dataset.replace('/', '_').replace(' ', '_')}.csv"


def _candidate_available() -> bool:
    return any((ROOT / "models_candidate").glob("*/feature_schema.json"))


def _route(dataset: str, ratio: float) -> Dict[str, Any]:
    if dataset == "CIC-IDS2017":
        return {"chosen_detector": "MutantShield production FusionEngine", "result_type": "production", "valid_for_final_claims": ratio >= 0.8}
    if dataset == "UNSW-NB15":
        return {"chosen_detector": "UNSW semantic mapped path", "result_type": "validation_only", "valid_for_final_claims": ratio >= 0.6, "warning": "UNSW is mapped, not native CIC."}
    if dataset == "CSE-CIC-IDS2018":
        return {"chosen_detector": "Production mapped path plus CSE repair candidate if available", "result_type": "production_and_candidate" if _candidate_available() else "production_only_candidate_missing", "valid_for_final_claims": ratio >= 0.8}
    if dataset == "DoHBrw":
        return {"chosen_detector": "DoHBrw native adapter; mapped CIC only as weak baseline", "result_type": "adapter", "valid_for_final_claims": True, "mapped_path_expected_weak": True}
    return {"chosen_detector": "unknown", "result_type": "unknown", "valid_for_final_claims": False}


def _audit_one(dataset: str) -> Dict[str, Any]:
    pd, err = import_pandas()
    if pd is None:
        return {"dataset": dataset, "status": "ERROR", "error": f"pandas_unavailable:{err}"}
    path = _csv(dataset)
    if not path.exists():
        return {"dataset": dataset, "status": "MISSING_EVAL_SET", "eval_csv": str(path)}
    df = pd.read_csv(path, low_memory=False)
    features = load_production_features()
    ratios = []
    zero_counts = []
    missing = Counter()
    sanitize = Counter()
    for _, row in df.head(200).iterrows():
        _mapped, quality = map_row_to_features(row, dataset, features)
        ratios.append(float(quality.get("mapped_ratio", 0.0)))
        zero_counts.append(int(quality.get("zero_filled_count", quality.get("missing_count", 0))))
        missing.update(quality.get("missing_features") or [])
        sanitize.update(quality.get("sanitization_counts") or {})
    ratio = round(sum(ratios) / max(1, len(ratios)), 4)
    zero_ratio = round((sum(zero_counts) / max(1, len(zero_counts))) / max(1, len(features)), 4)
    return {
        "dataset": dataset,
        "status": "PASS",
        "eval_csv": str(path),
        "rows": len(df),
        "label_distribution": {str(k): int(v) for k, v in df["y_true"].value_counts().to_dict().items()} if "y_true" in df else {},
        "feature_mapping_ratio": ratio,
        "zero_fill_ratio": zero_ratio,
        "missing_features_top": missing.most_common(20),
        "sanitizer_count": dict(sanitize),
        **_route(dataset, ratio),
    }


def run() -> Dict[str, Any]:
    results = {name: _audit_one(name) for name in DATASETS}
    report: Dict[str, Any] = {"generated_at": time.time(), "datasets": results}
    report["pass"] = all(item.get("status") in {"PASS", "MISSING_EVAL_SET"} for item in results.values())
    path = write_json("phase12_18b_detector_routing_audit.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B DETECTOR ROUTING AUDIT ===")
    for name, item in report["datasets"].items():
        print(f"{name}: {item.get('status')} detector={item.get('chosen_detector')} valid={item.get('valid_for_final_claims')}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
