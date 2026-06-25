"""Safe readers for ORACLE dashboard report files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = WORKSPACE_ROOT / "reports"
EVOLUTION_DIR = REPORTS_DIR / "evolution"


def _read_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, f"missing:{path.name}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data, None
        return {"data": data}, None
    except Exception as exc:
        return None, f"read_error:{path.name}:{exc!s}"


def load_report(relative: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    path = REPORTS_DIR / relative if not relative.startswith("evolution/") else REPORTS_DIR / relative
    if relative.startswith("evolution/"):
        path = REPORTS_DIR / relative
    else:
        path = REPORTS_DIR / relative
    return _read_json(path)


def _evolution_path(name: str) -> Path:
    return EVOLUTION_DIR / name


def collect_warnings(
    evolution: Dict[str, Any],
    chrono: Dict[str, Any],
    baseline: Optional[Dict[str, Any]],
) -> List[str]:
    warnings: List[str] = []
    if not evolution.get("promotion_allowed", True):
        warnings.append(
            "Model promotion is blocked until fair production baseline is validated."
        )
    if chrono.get("unverified_count", 0) > 0:
        warnings.append(
            "ChronoLedger evidence is unverified unless human reviewed."
        )
    gan_status = str(evolution.get("gan_status", ""))
    if gan_status in ("skipped_disabled", "not_available", "skipped"):
        warnings.append("GAN artifacts are not available.")
    art_status = str(evolution.get("art_status", ""))
    if art_status == "fallback":
        warnings.append(
            "IBM ART is not installed; fallback adversarial mutations used."
        )
    if baseline and baseline.get("baseline_quality_warning"):
        warnings.append(
            "Fair production baseline quality warning: unreliable or unfair evaluation."
        )
    if evolution.get("gan_training_required"):
        warnings.append("GAN training required before synthetic attack generation.")
    return warnings


def build_evolution_summary(
    evolution_report: Optional[Dict[str, Any]],
    eval_report: Optional[Dict[str, Any]],
    baseline: Optional[Dict[str, Any]],
    adversarial: Optional[Dict[str, Any]],
    gan: Optional[Dict[str, Any]],
    buffer: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    evo = evolution_report or {}
    evl = eval_report or {}
    return {
        "final_status": evo.get("final_status"),
        "dry_run": evo.get("dry_run"),
        "candidate_trained": evo.get("candidate_trained"),
        "candidate_id": evo.get("candidate_id"),
        "evaluation_passed": evo.get("evaluation_passed"),
        "promotion_allowed": evo.get("promotion_allowed", evl.get("promotion_allowed")),
        "promotion_status": evo.get("promotion_status", evl.get("promotion_status")),
        "baseline_quality_warning": evo.get(
            "baseline_quality_warning", evl.get("baseline_quality_warning", False)
        ),
        "gan_status": evo.get("gan_status"),
        "gan_training_required": evo.get("gan_training_required", (gan or {}).get("gan_training_required")),
        "art_status": evo.get("art_status"),
        "art_available": evo.get("art_available", (adversarial or {}).get("art_available")),
        "art_version": evo.get("art_version", (adversarial or {}).get("art_version")),
        "art_source": evo.get("art_source", (adversarial or {}).get("art_source")),
        "attacks_run": evo.get("attacks_run", (adversarial or {}).get("attacks_run", [])),
        "adversarial_accuracy": evo.get("adversarial_accuracy", (adversarial or {}).get("adversarial_accuracy")),
        "robustness_drop": evo.get("robustness_drop", (adversarial or {}).get("robustness_drop")),
        "adversarial_training_enabled": evo.get("adversarial_training_enabled"),
        "fair_baseline_reliable": evo.get(
            "fair_baseline_reliable", evl.get("fair_baseline_reliable", (baseline or {}).get("baseline_reliable"))
        ),
        "promoted": evo.get("promoted", False),
        "promotion_simulated": evo.get("promotion_simulated"),
        "datasets_used": evo.get("datasets_used", []),
        "supervised_buffer_count": evo.get("supervised_buffer_count", buffer.get("supervised_samples") if buffer else None),
        "anomaly_buffer_count": evo.get("anomaly_buffer_count"),
        "unverified_buffer_count": evo.get("unverified_buffer_count"),
        "adversarial_samples_generated": (adversarial or {}).get("adversarial_samples_generated"),
        "evaluation_reasons": evo.get("evaluation_reasons", evl.get("reasons", [])),
        "schema_compatible": evl.get("schema_compatible"),
        "baseline_present": evl.get("baseline_present"),
        "full_ensemble": evo.get("full_ensemble"),
        "models_trained_count": evo.get("models_trained_count"),
        "ensemble_promotion_ready": evo.get("ensemble_promotion_ready"),
        "global_adversarial_gate_passed": evo.get(
            "global_adversarial_gate_passed", (adversarial or {}).get("global_adversarial_gate_passed")
        ),
        "model_coverage": evo.get("model_coverage"),
        "adversarial_skipped": evo.get("adversarial_skipped"),
        "full_evolution_ready": bool(
            evo.get("full_ensemble")
            and evo.get("candidate_trained")
            and (
                evo.get("global_adversarial_gate_passed")
                or (adversarial or {}).get("global_adversarial_gate_passed")
            )
        ),
    }


def _is_evolution_ready(evolution: Dict[str, Any], coverage: Dict[str, Any]) -> bool:
    final_status = str(evolution.get("final_status") or "").upper()
    if final_status in {"PASS_DRY_RUN", "FULL_EVOLUTION_READY"}:
        return True
    if final_status.endswith("_READY"):
        return True
    if coverage.get("framework_final") is True:
        return True
    return bool(evolution.get("full_evolution_ready"))


def build_scheduler_summary(schedule: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    s = schedule or {}
    return {
        "enabled": s.get("enabled", False),
        "frequency": s.get("frequency", "manual"),
        "last_run": s.get("last_run"),
        "next_run": s.get("next_run"),
        "mode": s.get("mode", "candidate-only"),
        "adversarial_train": s.get("adversarial_train", True),
        "controlled_promotion_allowed": s.get("controlled_promotion_allowed", False),
        "status": s.get("status", "idle"),
    }


def build_model_coverage_summary(coverage: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    c = coverage or {}
    models = c.get("models") or []
    return {
        "models_trained_count": c.get("models_trained_count", 0),
        "promotion_eligible_count": c.get("promotion_eligible_count", 0),
        "full_ensemble_complete": c.get("full_ensemble_complete"),
        "ensemble_promotion_ready": c.get("ensemble_promotion_ready"),
        "per_model": [
            {
                "model_name": m.get("model_name"),
                "candidate_trained": m.get("candidate_trained"),
                "adversarial_evaluated": m.get("adversarial_evaluated"),
                "promotion_eligible": m.get("promotion_eligible"),
                "status": m.get("status"),
                "blocker_reason": m.get("blocker_reason"),
            }
            for m in models
        ],
    }


def build_chrono_summary(chrono: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    data = chrono or {}
    events = data.get("events") or []
    unverified = sum(1 for e in events if not e.get("human_reviewed", False))
    bucket_counts = data.get("bucket_counts") or {}
    return {
        "total_events": data.get("total_events", len(events)),
        "bucket_counts": bucket_counts,
        "unverified_count": unverified,
        "require_human_approval": data.get("require_human_approval_for_chrono", True),
        "false_positive_candidate": bucket_counts.get("false_positive_candidate", 0),
        "outlier_candidate": bucket_counts.get("outlier_candidate", 0),
    }


def build_performance_summary(
    validation: Optional[Dict[str, Any]],
    stress: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    val = validation or {}
    stress_summary = (stress or {}).get("summary") or stress or {}
    return {
        "avg_latency_ms": val.get("avg_latency_ms", stress_summary.get("avg_latency_ms")),
        "p95_latency_ms": val.get("p95_latency_ms", stress_summary.get("p95_latency_ms")),
        "max_latency_ms": val.get("max_latency_ms", stress_summary.get("max_latency_ms")),
        "success": val.get("success_count", stress_summary.get("success_count")),
        "degraded": val.get("degraded_count", stress_summary.get("degraded_count")),
        "failed": val.get("failed_count", stress_summary.get("failure_count", stress_summary.get("failed_count"))),
    }


def build_assurance_summary(validation: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    val = validation or {}
    return {
        "latest_completed": val.get("assurance_latest_completed"),
        "latest_pending": val.get("assurance_latest_pending"),
        "latest_failed": val.get("assurance_latest_failed"),
        "async_assurance_enabled": val.get("environment", {}).get("ORACLE_ASYNC_ASSURANCE") == "1",
    }


def build_ghosttunnel_summary(
    validation: Optional[Dict[str, Any]],
    benchmark: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    val = validation or {}
    bench = benchmark or {}
    fast_ack = bench.get("fast_ack") or bench
    return {
        "jobs_completed": val.get("ghosttunnel_jobs_completed"),
        "jobs_pending": val.get("ghosttunnel_jobs_pending", 0),
        "jobs_failed": val.get("ghosttunnel_jobs_failed", 0),
        "fast_ack_enabled": val.get("environment", {}).get("GHOSTTUNNEL_FAST_ACK") == "1",
        "avg_latency_ms": fast_ack.get("avg_latency_ms"),
        "ghosttunnel_avg_ms": fast_ack.get("ghosttunnel_avg_ms"),
    }


def build_module_health(validation: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    readiness = (validation or {}).get("backend_readiness", "UNKNOWN")
    ok = readiness == "READY"
    return {
        "oracle_core": ok,
        "mutantshield": ok,
        "qauthcore": ok,
        "ethicq": ok,
        "chronoledger": ok,
        "ghosttunnel": ok,
    }


def build_dashboard_summary() -> Dict[str, Any]:
    report_warnings: List[str] = []
    files = {
        "validation": _read_json(REPORTS_DIR / "oracle_backend_final_validation.json"),
        "stress": _read_json(REPORTS_DIR / "async_assurance_stress_100.json"),
        "ghosttunnel_bench": _read_json(REPORTS_DIR / "ghosttunnel_fast_ack_benchmark.json"),
        "evolution": _read_json(_evolution_path("evolution_run_report.json")),
        "evaluation": _read_json(_evolution_path("evaluation_gate_report.json")),
        "baseline": _read_json(_evolution_path("fair_production_baseline_metrics.json")),
        "baseline_legacy": _read_json(_evolution_path("production_baseline_metrics.json")),
        "art_setup": _read_json(_evolution_path("art_setup_report.json")),
        "adversarial": _read_json(_evolution_path("adversarial_hardening_report.json")),
        "gan": _read_json(_evolution_path("gan_generation_report.json")),
        "chrono": _read_json(_evolution_path("chronoledger_evidence.json")),
        "buffer": _read_json(_evolution_path("training_buffer_summary.json")),
        "schedule": _read_json(_evolution_path("evolution_schedule.json")),
        "model_coverage": _read_json(_evolution_path("model_coverage_report.json")),
        "full_adversarial": _read_json(_evolution_path("full_adversarial_report.json")),
    }

    parsed: Dict[str, Optional[Dict[str, Any]]] = {}
    for key, (data, err) in files.items():
        parsed[key] = data
        if err:
            report_warnings.append(err)

    validation = parsed["validation"]
    readiness = (validation or {}).get("backend_readiness", "UNKNOWN")
    backend_status = readiness if readiness in ("READY", "DEGRADED") else "UNKNOWN"
    if validation and validation.get("degraded_count", 0) > 0 and backend_status == "READY":
        backend_status = "DEGRADED"

    if not parsed["baseline"] and parsed.get("baseline_legacy"):
        parsed["baseline"] = parsed["baseline_legacy"]

    chrono_summary = build_chrono_summary(parsed["chrono"])
    evolution_summary = build_evolution_summary(
        parsed["evolution"],
        parsed["evaluation"],
        parsed["baseline"],
        parsed.get("full_adversarial") or parsed["adversarial"],
        parsed["gan"],
        parsed["buffer"],
    )
    if parsed.get("art_setup"):
        evolution_summary["art_version"] = (
            parsed["art_setup"].get("art_version")
            or (parsed.get("full_adversarial") or {}).get("art_version")
        )
    scheduler_summary = build_scheduler_summary(parsed.get("schedule"))
    coverage_summary = build_model_coverage_summary(parsed.get("model_coverage"))
    human_review_path = _evolution_path("human_review_queue.csv")
    human_review_count = 0
    if human_review_path.exists():
        human_review_count = max(0, len(human_review_path.read_text(encoding="utf-8").splitlines()) - 1)
    content_warnings = collect_warnings(
        evolution_summary,
        chrono_summary,
        parsed["baseline"],
    )

    assurance = build_assurance_summary(validation)
    ghosttunnel = build_ghosttunnel_summary(validation, parsed["ghosttunnel_bench"])

    evolution_ready = _is_evolution_ready(evolution_summary, coverage_summary)
    architecture_status = {
        "backend_ready": backend_status == "READY",
        "async_quantum_assurance_active": bool(assurance.get("async_assurance_enabled")),
        "ghosttunnel_fast_ack_active": bool(ghosttunnel.get("fast_ack_enabled")),
        "evolution_dry_run_pass": evolution_ready,
        "evolution_ready": evolution_ready,
        "promotion_blocked_safe": not bool(evolution_summary.get("promotion_allowed")),
    }

    return {
        "backend_status": backend_status,
        "modules": build_module_health(validation),
        "performance": build_performance_summary(validation, parsed["stress"]),
        "assurance": assurance,
        "ghosttunnel": ghosttunnel,
        "evolution": evolution_summary,
        "evolution_scheduler": scheduler_summary,
        "model_coverage": coverage_summary,
        "human_review_queue_count": human_review_count,
        "full_adversarial_gate": (parsed.get("full_adversarial") or {}).get("global_adversarial_gate_passed"),
        "chronoledger_evidence": chrono_summary,
        "warnings": content_warnings,
        "report_warnings": report_warnings,
        "architecture_status": architecture_status,
        "gui_alignment": {
            "evolution_engine_title": "MutantShield Evolution Engine",
            "evolution_engine_subtitle": (
                "Retraining, adversarial hardening, and promotion safety"
            ),
            "safety_controls_disabled": [
                "real_model_promotion",
                "force_promote",
                "auto_promote",
                "delete_logs",
                "delete_models",
            ],
        },
        "reports": {
            "backend_validation": "oracle_backend_final_validation.json",
            "evolution_run": "evolution/evolution_run_report.json",
            "evaluation_gate": "evolution/evaluation_gate_report.json",
            "production_baseline": "evolution/production_baseline_metrics.json",
            "chronoledger_evidence": "evolution/chronoledger_evidence.json",
        },
    }


def build_latest_events(limit: int = 20) -> Dict[str, Any]:
    chrono, err = _read_json(_evolution_path("chronoledger_evidence.json"))
    events: List[Dict[str, Any]] = []
    if chrono:
        raw = chrono.get("events") or []
        for e in sorted(raw, key=lambda x: x.get("timestamp", 0), reverse=True)[:limit]:
            events.append({
                "oracle_trace_id": e.get("oracle_trace_id"),
                "flow_id": e.get("flow_id"),
                "risk_label": e.get("risk_label"),
                "is_attack": e.get("is_attack"),
                "evidence_bucket": e.get("evidence_bucket"),
                "label_trust": e.get("label_trust"),
                "human_reviewed": e.get("human_reviewed"),
                "timestamp": e.get("timestamp"),
                "assurance_states": e.get("assurance_states"),
            })
    return {"events": events, "warning": err}
