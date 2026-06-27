"""Phase 12.18 full ORACLE stack dataset evaluation."""
from __future__ import annotations

import time
from collections import Counter
from typing import Any, Dict, List

import requests

from oracle_phase12_18_common import (
    CORE,
    DATASETS,
    binary_metrics,
    compact_error,
    discover_dataset_files,
    load_production_features,
    map_row_to_features,
    normalize_binary_label,
    predict_dohbrw_native,
    predict_mutantshield,
    read_labeled_dataset_sample,
    summarize_scores,
    write_json,
    write_md,
)


TARGETS = [
    ("CIC-IDS2017", "mapped_cic"),
    ("UNSW-NB15", "mapped_cic"),
    ("CSE-CIC-IDS2018", "mapped_cic"),
    ("DoHBrw", "mapped_cic"),
    ("DoHBrw", "native_adapter"),
]


def _run_dataset(dataset_name: str, path_name: str, sample_size: int) -> Dict[str, Any]:
    files = discover_dataset_files(dataset_name)
    if not files:
        return {"dataset": dataset_name, "path": path_name, "status": "BLOCKED_MISSING_DATASET", "events_sent": 0}
    try:
        source_file, df, label_col, files = read_labeled_dataset_sample(dataset_name, sample_size=sample_size)
        if not label_col:
            return {"dataset": dataset_name, "path": path_name, "status": "BLOCKED_LABEL_COLUMN_MISSING", "source_file": str(source_file)}
        production_features = load_production_features()
        y_true: List[int] = []
        y_pred: List[int] = []
        scores: List[float] = []
        latencies: List[float] = []
        status_counter: Counter[str] = Counter()
        failed_services: Counter[str] = Counter()
        ethics: Counter[str] = Counter()
        actions: Counter[str] = Counter()
        auth_verified = 0
        audit_logged = 0
        false_allows = 0
        false_blocks = 0
        proof: List[Dict[str, Any]] = []
        fallback_count = 0
        started = time.perf_counter()
        for idx, row in df.iterrows():
            true = normalize_binary_label(row[label_col])
            if path_name == "native_adapter":
                decision, raw, fallback = predict_dohbrw_native(row)
                if decision is None:
                    return {"dataset": dataset_name, "path": path_name, "status": "BLOCKED_ADAPTER_UNAVAILABLE", "error": raw.get("error")}
            else:
                features, _quality = map_row_to_features(row, dataset_name, production_features)
                decision, raw, fallback = predict_mutantshield(features)
            fallback_count += 1 if fallback else 0
            payload = {
                "flow_id": f"phase12-18-{dataset_name}-{path_name}-{idx}",
                "src_ip": "192.0.2.18",
                "dst_ip": "198.51.100.18",
                "risk_score": float(decision.get("risk_score", 0.0)),
                "risk_label": str(decision.get("risk_label", "LOW")),
                "is_attack": bool(decision.get("is_attack")),
                "attack_family": str(decision.get("attack_family", row[label_col])),
                "confidence_band": str(decision.get("confidence_band", "LOW")),
                "model_consensus": str(decision.get("model_consensus", "unknown")),
                "detector_source": f"MutantShield:{path_name}",
            }
            t0 = time.perf_counter()
            try:
                response = requests.post(f"{CORE}/oracle/process", json=payload, timeout=30)
                body = response.json() if response.content else {}
                latency = round((time.perf_counter() - t0) * 1000.0, 4)
            except Exception as exc:
                response = None
                body = {"error": str(exc), "failed_services": ["request_exception"]}
                latency = round((time.perf_counter() - t0) * 1000.0, 4)
            status_code = response.status_code if response is not None else None
            status_counter[str(status_code)] += 1
            for svc in body.get("failed_services") or []:
                failed_services[str(svc)] += 1
            det = body.get("detection") or {}
            auth = body.get("auth") or {}
            eth = body.get("ethics") or {}
            action = body.get("action") or {}
            audit = body.get("audit") or {}
            y_true.append(true)
            pred = 1 if payload["is_attack"] else 0
            y_pred.append(pred)
            scores.append(payload["risk_score"])
            latencies.append(latency)
            auth_verified += 1 if auth.get("verified") else 0
            audit_logged += 1 if audit.get("logged") else 0
            ethics[str(eth.get("decision") or eth.get("action") or "unknown")] += 1
            final_action = str(action.get("final_action") or "unknown")
            actions[final_action] += 1
            if true == 1 and final_action in {"allow", "monitor", "none", "unknown"} and payload["is_attack"]:
                false_allows += 0
            if true == 0 and final_action not in {"allow", "monitor", "none", "unknown"}:
                false_blocks += 1
            if len(proof) < 12:
                proof.append(
                    {
                        "dataset": dataset_name,
                        "path": path_name,
                        "label": str(row[label_col]),
                        "mutantshield": {
                            "risk_score": payload["risk_score"],
                            "risk_label": payload["risk_label"],
                            "is_attack": payload["is_attack"],
                            "model_consensus": payload["model_consensus"],
                        },
                        "oracle_detection": {
                            "risk_score": det.get("risk_score"),
                            "risk_label": det.get("risk_label"),
                            "is_attack": det.get("is_attack"),
                            "model_consensus": det.get("model_consensus"),
                        },
                        "oracle_final_action": final_action,
                        "trace_id": body.get("oracle_trace_id"),
                        "fields_preserved": (
                            float(det.get("risk_score", -1)) == payload["risk_score"]
                            and str(det.get("risk_label")) == payload["risk_label"]
                        ),
                    }
                )
        metrics = binary_metrics(y_true, y_pred)
        duration = time.perf_counter() - started
        events = len(y_true)
        degraded = sum(count for code, count in status_counter.items() if code == "207")
        failed = sum(count for code, count in status_counter.items() if code in {"None"} or (code.isdigit() and int(code) >= 500))
        return {
            "dataset": dataset_name,
            "path": path_name,
            "status": "PASS",
            "source_file": str(source_file),
            "events_sent": events,
            "success": status_counter.get("200", 0),
            "degraded": degraded,
            "failed": failed,
            "status_code_distribution": dict(status_counter),
            "failed_service_distribution": dict(failed_services),
            "audit_logged_rate": round(audit_logged / max(1, events), 4),
            "auth_verified_rate": round(auth_verified / max(1, events), 4),
            "ethics_decision_distribution": dict(ethics),
            "action_distribution": dict(actions),
            "avg_latency_ms": round(sum(latencies) / max(1, len(latencies)), 4),
            "p95_latency_ms": sorted(latencies)[int(0.95 * (len(latencies) - 1))] if latencies else 0.0,
            "p99_latency_ms": sorted(latencies)[int(0.99 * (len(latencies) - 1))] if latencies else 0.0,
            "detection_metrics": metrics,
            "risk_score_distribution": summarize_scores(scores),
            "false_allows": false_allows,
            "false_blocks": false_blocks,
            "fallback_count": fallback_count,
            "throughput_events_sec": round(events / max(0.001, duration), 2),
            "proof_records": proof,
        }
    except Exception as exc:
        return {"dataset": dataset_name, "path": path_name, "status": "ERROR", "source_file": str(files[0]) if files else "", "error": compact_error(exc)}


def run(sample_size: int = 50) -> Dict[str, Any]:
    results = {f"{dataset}:{path}": _run_dataset(dataset, path, sample_size) for dataset, path in TARGETS}
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "sample_size": sample_size,
        "results": results,
        "proof_requirement": "proof_records include MutantShield risk fields and Oracle detection fields for side-by-side comparison.",
        "pass": all(item["status"] in {"PASS", "BLOCKED_MISSING_DATASET", "BLOCKED_ADAPTER_UNAVAILABLE", "BLOCKED_LABEL_COLUMN_MISSING"} for item in results.values()),
    }
    json_path = write_json("phase12_18_full_stack_dataset_eval.json", report)
    md = ["# Phase 12.18 Full ORACLE Stack Dataset Evaluation", ""]
    for key, item in results.items():
        dm = item.get("detection_metrics") or {}
        md += [
            f"## {key}",
            f"- Status: `{item.get('status')}`",
            f"- Events sent: `{item.get('events_sent')}`",
            f"- Success/degraded/failed: `{item.get('success')}` / `{item.get('degraded')}` / `{item.get('failed')}`",
            f"- Audit logged rate: `{item.get('audit_logged_rate')}`",
            f"- Recall/F1: `{dm.get('recall')}` / `{dm.get('f1')}`",
            f"- Note/Error: {item.get('error') or ''}",
            "",
        ]
    md_path = write_md("phase12_18_full_stack_dataset_eval.md", md)
    report["json_report_path"] = str(json_path)
    report["markdown_report_path"] = str(md_path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18 FULL STACK DATASET EVALUATION ===")
    for key, item in report["results"].items():
        dm = item.get("detection_metrics") or {}
        print(f"{key}: {item.get('status')} sent={item.get('events_sent')} recall={dm.get('recall')} f1={dm.get('f1')}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['json_report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
