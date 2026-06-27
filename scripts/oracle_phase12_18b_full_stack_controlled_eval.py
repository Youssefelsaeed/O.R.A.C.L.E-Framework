"""Controlled full-stack ORACLE evaluation using detector outputs."""
from __future__ import annotations

import time
from collections import Counter
from typing import Any, Dict, List

import requests

from oracle_phase12_18_common import CORE, binary_metrics, import_pandas, load_production_features, per_family_recall, summarize_scores, write_json, write_md
from oracle_phase12_18b_mutantshield_controlled_eval import PATHS, _candidate_available, _csv, _predict

MAX_ROWS_PER_PATH = 100


def _runtime_current() -> Dict[str, Any]:
    try:
        runtime = requests.get(f"{CORE}/oracle/runtime-info", timeout=10).json()
        health = requests.get(f"{CORE}/health", timeout=10).json()
        ok = runtime.get("code_marker") == "phase12_18b_runtime" and health.get("code_marker") == "phase12_18b_runtime"
        return {"ok": ok, "runtime": runtime, "health": health}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _sample(df: Any):
    if len(df) <= MAX_ROWS_PER_PATH:
        return df
    benign = df[df["y_true"] == 0]
    attack = df[df["y_true"] == 1]
    parts = []
    if not benign.empty:
        parts.append(benign.sample(n=min(MAX_ROWS_PER_PATH // 2, len(benign)), random_state=1218))
    if not attack.empty:
        parts.append(attack.sample(n=min(MAX_ROWS_PER_PATH - sum(len(p) for p in parts), len(attack)), random_state=1218))
    if parts:
        import pandas as pd

        return pd.concat(parts).sample(frac=1.0, random_state=1218)
    return df.head(MAX_ROWS_PER_PATH)


def _eval(dataset: str, path_name: str) -> Dict[str, Any]:
    pd, err = import_pandas()
    if pd is None:
        return {"dataset": dataset, "path": path_name, "status": "ERROR", "error": f"pandas_unavailable:{err}"}
    csv = _csv(dataset)
    if not csv.exists():
        return {"dataset": dataset, "path": path_name, "status": "MISSING_EVAL_SET"}
    if path_name == "cse_repair_candidate" and not _candidate_available():
        return {"dataset": dataset, "path": path_name, "status": "CANDIDATE_UNAVAILABLE"}
    df = _sample(pd.read_csv(csv, low_memory=False))
    features = load_production_features()
    y_true: List[int] = []
    y_pred: List[int] = []
    labels: List[str] = []
    scores: List[float] = []
    latencies: List[float] = []
    codes = Counter()
    failed_services = Counter()
    ethics = Counter()
    actions = Counter()
    audit_logged = auth_verified = fields_preserved = 0
    proof = []
    for idx, row in df.iterrows():
        decision, raw, fallback = _predict(row, dataset, path_name, features)
        if decision is None:
            return {"dataset": dataset, "path": path_name, "status": "DETECTOR_UNAVAILABLE", "error": raw.get("error")}
        payload = {"flow_id": f"phase12-18b-{dataset}-{path_name}-{idx}", "src_ip": "192.0.2.218", "dst_ip": "198.51.100.218", "risk_score": float(decision.get("risk_score", 0.0)), "risk_label": str(decision.get("risk_label", "LOW")), "is_attack": bool(decision.get("is_attack")), "attack_family": str(decision.get("attack_family") or row.get("attack_family") or row.get("original_label")), "confidence_band": str(decision.get("confidence_band", "LOW")), "model_consensus": str(decision.get("model_consensus", "unknown")), "detector_source": path_name, "dataset_source": dataset, "y_true": int(row["y_true"])}
        t0 = time.perf_counter()
        try:
            resp = requests.post(f"{CORE}/oracle/process", json=payload, timeout=30)
            body = resp.json() if resp.content else {}
            code = resp.status_code
        except Exception as exc:
            body = {"failed_services": ["request_exception"], "error": str(exc)}
            code = None
        latency = round((time.perf_counter() - t0) * 1000.0, 4)
        det = body.get("detection") or {}
        auth = body.get("auth") or {}
        eth = body.get("ethics") or {}
        action = body.get("action") or {}
        audit = body.get("audit") or {}
        preserved = abs(float(det.get("risk_score", -999)) - payload["risk_score"]) <= 1e-9 and str(det.get("risk_label")) == payload["risk_label"] and str(det.get("attack_family")) == payload["attack_family"]
        fields_preserved += 1 if preserved else 0
        codes[str(code)] += 1
        for svc in body.get("failed_services") or []:
            failed_services[str(svc)] += 1
        audit_logged += 1 if audit.get("logged") else 0
        auth_verified += 1 if auth.get("verified") else 0
        final_action = str(action.get("final_action") or "unknown")
        ethics[str(eth.get("decision") or eth.get("action") or "unknown")] += 1
        actions[final_action] += 1
        true = int(row["y_true"])
        pred = 1 if payload["is_attack"] else 0
        y_true.append(true); y_pred.append(pred); labels.append(str(row.get("attack_family") or row.get("original_label"))); scores.append(payload["risk_score"]); latencies.append(latency)
        if len(proof) < 10:
            proof.append({"dataset_source": dataset, "y_true": true, "original_label": row.get("original_label"), "detector_used": path_name, "detector_risk_score": payload["risk_score"], "detector_risk_label": payload["risk_label"], "oracle_risk_score": det.get("risk_score"), "oracle_risk_label": det.get("risk_label"), "final_action": final_action, "audit_logged": audit.get("logged"), "trace_id": body.get("oracle_trace_id"), "fields_preserved": preserved})
    metrics = binary_metrics(y_true, y_pred)
    metrics["per_attack_family_recall"] = per_family_recall(labels, y_true, y_pred)
    total = len(y_true)
    failed = sum(v for k, v in codes.items() if k == "None" or (k.isdigit() and int(k) >= 500))
    return {"dataset": dataset, "path": path_name, "status": "PASS" if len(set(y_true)) == 2 else "LIMITED_UNBALANCED", "events_sent": total, "success": codes.get("200", 0), "degraded": codes.get("207", 0), "failed": failed, "status_code_distribution": dict(codes), "failed_service_distribution": dict(failed_services), "field_preservation_rate": round(fields_preserved / max(1, total), 4), "audit_logged_rate": round(audit_logged / max(1, total), 4), "auth_verified_rate": round(auth_verified / max(1, total), 4), "ethics_decision_distribution": dict(ethics), "final_action_distribution": dict(actions), "avg_latency_ms": round(sum(latencies) / max(1, len(latencies)), 4), "p95_latency_ms": sorted(latencies)[int(0.95 * (len(latencies) - 1))] if latencies else 0.0, "p99_latency_ms": sorted(latencies)[int(0.99 * (len(latencies) - 1))] if latencies else 0.0, "detection_metrics": metrics, "risk_score_distribution": summarize_scores(scores), "proof_records": proof}


def run() -> Dict[str, Any]:
    runtime = _runtime_current()
    if not runtime.get("ok"):
        report: Dict[str, Any] = {"generated_at": time.time(), "status": "BLOCKED_RUNTIME_NOT_CURRENT", "runtime_proof": runtime, "max_rows_per_path": MAX_ROWS_PER_PATH, "results": {}, "pass": False}
        json_path = write_json("phase12_18b_full_stack_controlled_eval.json", report)
        md_path = write_md("phase12_18b_full_stack_controlled_eval.md", ["# Phase 12.18B Full Stack Controlled Evaluation", "", "Status: `BLOCKED_RUNTIME_NOT_CURRENT`", "", "The evaluator did not send controlled rows because `/oracle/runtime-info` did not prove the Phase 12.18B runtime marker."])
        report["json_report_path"] = str(json_path); report["markdown_report_path"] = str(md_path)
        return report
    results = {f"{d}:{p}": _eval(d, p) for d, p in PATHS}
    report: Dict[str, Any] = {"generated_at": time.time(), "max_rows_per_path": MAX_ROWS_PER_PATH, "results": results}
    report["pass"] = all(v.get("status") in {"PASS", "LIMITED_UNBALANCED", "CANDIDATE_UNAVAILABLE", "MISSING_EVAL_SET"} for v in results.values())
    json_path = write_json("phase12_18b_full_stack_controlled_eval.json", report)
    lines = ["# Phase 12.18B Full Stack Controlled Evaluation", ""]
    for key, item in results.items():
        m = item.get("detection_metrics") or {}
        lines += [f"## {key}", f"- Status: `{item.get('status')}`", f"- Sent: `{item.get('events_sent')}`", f"- Success/degraded/failed: `{item.get('success')}` / `{item.get('degraded')}` / `{item.get('failed')}`", f"- Recall/F1: `{m.get('recall')}` / `{m.get('f1')}`", f"- Field preservation: `{item.get('field_preservation_rate')}`", ""]
    md_path = write_md("phase12_18b_full_stack_controlled_eval.md", lines)
    report["json_report_path"] = str(json_path); report["markdown_report_path"] = str(md_path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B FULL STACK CONTROLLED EVAL ===")
    for key, item in report["results"].items():
        m = item.get("detection_metrics") or {}
        print(f"{key}: {item.get('status')} sent={item.get('events_sent')} recall={m.get('recall')} f1={m.get('f1')} preserved={item.get('field_preservation_rate')}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['json_report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
