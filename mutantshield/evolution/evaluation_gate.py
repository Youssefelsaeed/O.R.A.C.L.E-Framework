"""Evaluation gate — candidate must pass fair production baseline comparison before promotion."""

from __future__ import annotations



import json

import time

from pathlib import Path

from typing import Any, Dict, List, Optional, Tuple



import joblib

import numpy as np

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score



from .config import EvolutionConfig

from .reports import read_json, write_json

from .schema_validation import validate_feature_schema



REQUIRED_SOURCE_CHECKS = (

    "dataset:CIC-IDS2017",

    "dataset:UNSW-NB15",

)



FAIR_BASELINE_PATH = "fair_production_baseline_metrics.json"

LEGACY_BASELINE_PATH = "production_baseline_metrics.json"





def _evaluate_classifier(model, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:

    preds = model.predict(X)

    if hasattr(preds, "ndim") and preds.ndim > 1:

        preds = preds.argmax(axis=1)

    preds = np.asarray(preds).astype(int)

    y = np.asarray(y).astype(int)

    acc = float(accuracy_score(y, preds))

    prec = float(precision_score(y, preds, zero_division=0))

    rec = float(recall_score(y, preds, zero_division=0))

    f1 = float(f1_score(y, preds, zero_division=0))

    fp = int(((preds == 1) & (y == 0)).sum())

    fn = int(((preds == 0) & (y == 1)).sum())

    tn = int(((preds == 0) & (y == 0)).sum())

    fpr = float(fp / max(1, fp + tn))

    fnr = float(fn / max(1, fn + int((y == 1).sum())))

    return {

        "sample_count": int(len(y)),

        "accuracy": round(acc, 4),

        "precision": round(prec, 4),

        "recall": round(rec, 4),

        "f1": round(f1, 4),

        "false_positive_rate": round(fpr, 4),

        "false_negative_rate": round(fnr, 4),

    }





def _load_baseline_metrics(cfg: EvolutionConfig) -> Tuple[Optional[Dict[str, Any]], str]:

    fair_path = cfg.reports_dir / FAIR_BASELINE_PATH

    if fair_path.exists():

        data = read_json(fair_path)

        if data.get("f1") is not None or data.get("by_source"):

            data["baseline_source_type"] = "fair"

            return data, "fair"



    legacy_path = cfg.reports_dir / LEGACY_BASELINE_PATH

    if legacy_path.exists():

        data = read_json(legacy_path)

        if data.get("f1") is not None:

            data["baseline_source_type"] = "legacy"

            return data, "legacy"

    return None, "missing"





def _load_candidate_feature_schema(candidate_result: Dict[str, Any]) -> List[str]:

    feature_cols = candidate_result.get("feature_cols") or []

    if feature_cols:

        return [str(f).strip() for f in feature_cols]

    candidate_dir = candidate_result.get("candidate_dir")

    if candidate_dir:

        schema_path = Path(candidate_dir) / "feature_schema.json"

        if schema_path.exists():

            data = json.loads(schema_path.read_text(encoding="utf-8"))

            return [str(f).strip() for f in data.get("features", [])]

    return []





def _compare_against_baseline(

    cand: Dict[str, Any],

    base: Dict[str, Any],

    label: str,

) -> Tuple[bool, List[str]]:

    reasons: List[str] = []

    ok = True

    base_f1 = float(base.get("f1", 0))

    cand_f1 = float(cand.get("f1", 0))

    base_fpr = float(base.get("false_positive_rate", 0))

    cand_fpr = float(cand.get("false_positive_rate", 0))



    if base_f1 > 0 and cand_f1 < base_f1 * 0.95:

        ok = False

        reasons.append(f"{label}:f1_drop>5%")

    if cand_fpr > base_fpr + 0.05:

        ok = False

        reasons.append(f"{label}:fpr_increase>5%")

    return ok, reasons





def _metrics_from_predictions(y_arr: np.ndarray, p_arr: np.ndarray) -> Dict[str, Any]:

    fp = int(((p_arr == 1) & (y_arr == 0)).sum())

    fn = int(((p_arr == 0) & (y_arr == 1)).sum())

    tn = int(((p_arr == 0) & (y_arr == 0)).sum())

    return {

        "sample_count": int(len(y_arr)),

        "accuracy": round(float(accuracy_score(y_arr, p_arr)), 4),

        "precision": round(float(precision_score(y_arr, p_arr, zero_division=0)), 4),

        "recall": round(float(recall_score(y_arr, p_arr, zero_division=0)), 4),

        "f1": round(float(f1_score(y_arr, p_arr, zero_division=0)), 4),

        "false_positive_rate": round(float(fp / max(1, fp + tn)), 4),

        "false_negative_rate": round(float(fn / max(1, fn + int((y_arr == 1).sum()))), 4),

    }





def _candidate_by_source(

    model,

    X: np.ndarray,

    y: np.ndarray,

    sources: List[str],

) -> Dict[str, Dict[str, Any]]:

    if len(sources) != len(X):

        return {}



    out: Dict[str, Dict[str, Any]] = {}

    for src in set(sources):

        idx = [i for i, s in enumerate(sources) if s == src]

        if len(idx) < 5:

            continue

        split = max(1, int(len(idx) * 0.8))

        test_idx = idx[split:]

        if len(test_idx) < 3:

            test_idx = idx

        X_sub = X[test_idx]

        y_sub = np.asarray(y[test_idx]).astype(int)

        preds = model.predict(X_sub)

        if hasattr(preds, "ndim") and preds.ndim > 1:

            preds = preds.argmax(axis=1)

        out[src] = _metrics_from_predictions(y_sub, np.asarray(preds).astype(int))

    return out





def _adversarial_hardening_critical(adversarial_report: Dict[str, Any]) -> bool:

    if not adversarial_report:

        return False

    if adversarial_report.get("recommendation") == "art_disabled":

        return False

    drop = adversarial_report.get("robustness_drop")

    if drop is not None and float(drop) > 0.5:

        return True

    if adversarial_report.get("errors") and adversarial_report.get("adversarial_samples_generated", 0) == 0:

        return True

    return False





def run_evaluation_gate(
    cfg: EvolutionConfig,
    candidate_result: Dict[str, Any],
    adversarial_report: Dict[str, Any],
    coverage_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    metadata = candidate_result.get("metadata", {})

    X = candidate_result.get("X")

    y = candidate_result.get("y")

    sources = candidate_result.get("sources") or []

    reasons: List[str] = []

    passed = True

    promotion_allowed = False

    promotion_status = "pending"



    candidate_metrics: Dict[str, Any] = {}

    candidate_by_source: Dict[str, Dict[str, Any]] = {}

    sample_count = int(metadata.get("sample_count", 0))

    if X is not None and y is not None and len(X) > 10:

        split = max(10, int(len(X) * 0.8))

        X_te, y_te = X[split:], y[split:]

        if len(X_te) < 5:

            X_te, y_te = X, y

        artifacts = metadata.get("artifacts", {})

        if artifacts.get("xgboost"):

            model = joblib.load(artifacts["xgboost"])

            candidate_metrics = _evaluate_classifier(model, X_te, y_te)

            t0 = time.perf_counter()

            n = min(50, len(X_te))

            _ = model.predict(X_te[:n])

            candidate_metrics["inference_latency_ms"] = round((time.perf_counter() - t0) * 1000.0 / max(1, n), 3)

            if sources and len(sources) == len(X):

                candidate_by_source = _candidate_by_source(model, X, y, sources)



    baseline_metrics, baseline_type = _load_baseline_metrics(cfg)

    baseline_by_source = dict((baseline_metrics or {}).get("by_source") or {})

    fair_baseline_reliable = bool((baseline_metrics or {}).get("baseline_reliable", False))

    baseline_quality_warning = bool((baseline_metrics or {}).get("baseline_quality_warning", False))

    if baseline_metrics is not None and float(baseline_metrics.get("f1", 0)) == 0.0:

        baseline_quality_warning = True



    production_features = list((baseline_metrics or {}).get("feature_schema") or [])

    candidate_features = _load_candidate_feature_schema(candidate_result)

    schema_report = validate_feature_schema(candidate_features, production_features) if production_features else {

        "compatible": bool(metadata.get("schema_compatible", True)),

        "status": "no_production_schema",

        "missing_in_candidate": [],

        "extra_in_candidate": [],

    }

    schema_compatible = bool(schema_report.get("compatible", False)) if production_features else bool(metadata.get("schema_compatible", True))



    sample_ok = sample_count >= min(50, cfg.min_samples) or (X is not None and len(X) >= min(50, cfg.min_samples))



    if not sample_ok:

        passed = False

        reasons.append(f"sample_count<{min(50, cfg.min_samples)}")

    if not schema_compatible:

        passed = False

        reasons.append("schema_mismatch")

        promotion_status = "promotion_blocked_schema_mismatch"

        if schema_report.get("missing_in_candidate"):

            reasons.append(f"missing_features:{len(schema_report['missing_in_candidate'])}")

    if not candidate_metrics:

        passed = False

        reasons.append("no_candidate_metrics")



    adv_critical = _adversarial_hardening_critical(adversarial_report)

    if cfg.skip_adversarial:
        promotion_allowed = False
        promotion_status = "promotion_blocked_adversarial_skipped"
        reasons.append("promotion_blocked_adversarial_skipped")

    if adversarial_report.get("adversarial_skipped"):
        promotion_allowed = False
        promotion_status = "promotion_blocked_adversarial_skipped"
        reasons.append("promotion_blocked_adversarial_skipped")

    if not adversarial_report.get("global_adversarial_gate_passed", True) and not cfg.skip_adversarial:
        adv_critical = True
        reasons.append("promotion_blocked_adversarial_gate")

    coverage = coverage_report or {}
    if coverage and not coverage.get("ensemble_promotion_ready") and cfg.mode == "controlled-promotion":
        reasons.append("promotion_blocked_incomplete_ensemble")
        promotion_allowed = False
        if promotion_status == "pending":
            promotion_status = "promotion_blocked_incomplete_ensemble"

    source_comparison: Dict[str, Dict[str, Any]] = {}

    if baseline_type == "missing":

        reasons.append("promotion_blocked_missing_fair_baseline")

        promotion_status = "promotion_blocked_missing_fair_baseline"

        promotion_allowed = False

    elif baseline_type == "fair" and not fair_baseline_reliable:

        reasons.append("promotion_blocked_unreliable_fair_baseline")

        promotion_status = "promotion_blocked_unreliable_fair_baseline"

        promotion_allowed = False

        baseline_quality_warning = True

    elif baseline_metrics is None:

        reasons.append("promotion_blocked_no_baseline")

        promotion_status = "promotion_blocked_no_baseline"

        promotion_allowed = False

    else:

        global_ok, global_reasons = _compare_against_baseline(candidate_metrics, baseline_metrics, "global")

        if not global_ok:

            passed = False

            reasons.extend(global_reasons)



        for src in REQUIRED_SOURCE_CHECKS:

            base_src = baseline_by_source.get(src)

            cand_src = candidate_by_source.get(src)

            if not base_src:

                continue

            if not base_src.get("reliable", True) and float(base_src.get("f1", 0)) == 0.0:

                baseline_quality_warning = True

                reasons.append(f"{src}:baseline_source_unreliable")

            if not cand_src:

                passed = False

                reasons.append(f"{src}:no_candidate_metrics")

                source_comparison[src] = {

                    "passed": False,

                    "baseline": base_src,

                    "candidate": cand_src,

                    "reasons": [f"{src}:no_candidate_metrics"],

                }

                continue

            src_ok, src_reasons = _compare_against_baseline(cand_src, base_src, src)

            source_comparison[src] = {

                "passed": src_ok,

                "baseline": base_src,

                "candidate": cand_src,

                "reasons": src_reasons,

            }

            if not src_ok:

                passed = False

                reasons.extend(src_reasons)



        base_lat = float(baseline_metrics.get("inference_latency_ms", 0))

        cand_lat = float(candidate_metrics.get("inference_latency_ms", 0))

        if base_lat > 0 and cand_lat > base_lat * 1.5:

            passed = False

            reasons.append("latency_regression>50%")



        if adv_critical:

            promotion_allowed = False

            promotion_status = "promotion_blocked_adversarial_hardening"

            reasons.append("promotion_blocked_adversarial_hardening")

        elif baseline_quality_warning and not fair_baseline_reliable and not cfg.force_promote:

            promotion_allowed = False

            promotion_status = "promotion_blocked_unfair_baseline"

            reasons.append("promotion_blocked_unfair_baseline")

        elif not fair_baseline_reliable and baseline_type == "fair" and not cfg.force_promote:

            promotion_allowed = False

            promotion_status = "promotion_blocked_unreliable_fair_baseline"

        elif passed and fair_baseline_reliable and not cfg.force_promote:

            promotion_allowed = True

            promotion_status = "promotion_allowed"

        elif passed and cfg.force_promote:

            promotion_allowed = True

            promotion_status = "force_promote_allowed"

        else:

            promotion_allowed = False

            promotion_status = "promotion_blocked_metrics"



    if cfg.mode == "controlled-promotion" and not cfg.human_approval_token:

        promotion_allowed = False

        promotion_status = "promotion_blocked_missing_human_approval"

        reasons.append("promotion_blocked_missing_human_approval")



    if cfg.mode in ("dry-run", "candidate-only"):

        promotion_allowed = False

        if promotion_status == "promotion_allowed":

            promotion_status = "promotion_blocked_dry_run_mode"



    adv_acc = adversarial_report.get("adversarial_accuracy")

    if adv_acc is not None:

        candidate_metrics["adversarial_accuracy"] = adv_acc



    latency = float(candidate_metrics.get("inference_latency_ms", 0))

    if latency > 500:

        passed = False

        reasons.append("inference_latency_too_high")

        promotion_allowed = False

        promotion_status = "promotion_blocked_latency"



    report = {

        "generated_at": time.time(),

        "passed": passed,

        "promotion_allowed": promotion_allowed,

        "promotion_status": promotion_status,

        "dry_run": cfg.dry_run,

        "mode": cfg.mode,

        "reasons": reasons,

        "metrics": candidate_metrics,

        "baseline_metrics": baseline_metrics,

        "baseline_source_type": baseline_type,

        "fair_baseline_reliable": fair_baseline_reliable,

        "candidate_metrics": candidate_metrics,

        "candidate_by_source": candidate_by_source,

        "source_comparison": source_comparison if baseline_metrics else {},

        "schema_compatible": schema_compatible,

        "schema_validation": schema_report,

        "sample_count": sample_count or (len(X) if X is not None else 0),

        "baseline_source": str(cfg.reports_dir / (FAIR_BASELINE_PATH if baseline_type == "fair" else LEGACY_BASELINE_PATH)),

        "baseline_present": baseline_metrics is not None,

        "baseline_quality_warning": baseline_quality_warning,

        "adversarial_hardening_critical": adv_critical,

    }

    write_json(cfg.reports_dir / "evaluation_gate_report.json", report)

    return report


