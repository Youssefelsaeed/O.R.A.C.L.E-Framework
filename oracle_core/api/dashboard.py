"""ORACLE dashboard API — reads report files and exposes safe GUI endpoints."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from ..dashboard_reports import (
    REPORTS_DIR,
    WORKSPACE_ROOT,
    build_chrono_summary,
    build_dashboard_summary,
    build_evolution_summary,
    build_latest_events,
    build_performance_summary,
    _read_json,
    _evolution_path,
)

router = APIRouter(prefix="/oracle/dashboard", tags=["dashboard"])

REPORT_FILES: Dict[str, Path] = {
    "backend_validation": REPORTS_DIR / "oracle_backend_final_validation.json",
    "evolution_run": _evolution_path("evolution_run_report.json"),
    "evaluation_gate": _evolution_path("evaluation_gate_report.json"),
    "production_baseline": _evolution_path("production_baseline_metrics.json"),
    "chronoledger_evidence": _evolution_path("chronoledger_evidence.json"),
}


@router.get("/summary")
async def dashboard_summary() -> Dict[str, Any]:
    return build_dashboard_summary()


@router.get("/health")
async def dashboard_health() -> Dict[str, Any]:
    summary = build_dashboard_summary()
    return {
        "backend_status": summary["backend_status"],
        "modules": summary["modules"],
        "warnings": summary["warnings"],
        "report_warnings": summary["report_warnings"],
        "assurance": summary["assurance"],
    }


@router.get("/module-status")
async def dashboard_module_status() -> Dict[str, Any]:
    summary = build_dashboard_summary()
    latest = build_latest_events(limit=5)
    return {
        "backend_status": summary["backend_status"],
        "modules": summary["modules"],
        "monitoring": {
            "live_network_capture": "NOT_ACTIVE",
            "realtime_replay": "LAST_RUN" if any(
                "LIVE_REPLAY" in str(event.get("data_source", "")) for event in latest.get("events", [])
            ) else "NOT_RUN",
            "latest_event_source": (latest.get("events") or [{}])[0].get("data_source", "REPORT"),
            "last_trace_id": (latest.get("events") or [{}])[0].get("oracle_trace_id"),
            "last_event_timestamp": (latest.get("events") or [{}])[0].get("timestamp"),
            "note": "Live network capture is not active unless sensor readiness reports ready; realtime replay proof is the validated safe live proof.",
        },
        "latest_events": latest.get("events", []),
    }


@router.get("/performance")
async def dashboard_performance() -> Dict[str, Any]:
    validation, w1 = _read_json(REPORTS_DIR / "oracle_backend_final_validation.json")
    stress, w2 = _read_json(REPORTS_DIR / "async_assurance_stress_100.json")
    ghost, w3 = _read_json(REPORTS_DIR / "ghosttunnel_fast_ack_benchmark.json")
    warnings = [w for w in (w1, w2, w3) if w]
    return {
        "performance": build_performance_summary(validation, stress),
        "ghosttunnel_benchmark": ghost,
        "validation_checks": (validation or {}).get("checks"),
        "warnings": warnings,
    }


@router.get("/evolution")
async def dashboard_evolution() -> Dict[str, Any]:
    summary = build_dashboard_summary()
    evolution, w1 = _read_json(_evolution_path("evolution_run_report.json"))
    evaluation, w2 = _read_json(_evolution_path("evaluation_gate_report.json"))
    baseline, w3 = _read_json(_evolution_path("fair_production_baseline_metrics.json"))
    if not baseline:
        baseline, w3 = _read_json(_evolution_path("production_baseline_metrics.json"))
    adversarial, w4 = _read_json(_evolution_path("full_adversarial_report.json"))
    if not adversarial:
        adversarial, w4 = _read_json(_evolution_path("adversarial_hardening_report.json"))
    gan, w5 = _read_json(_evolution_path("gan_generation_report.json"))
    buffer, w6 = _read_json(_evolution_path("training_buffer_summary.json"))
    art_setup, w7 = _read_json(_evolution_path("art_setup_report.json"))
    warnings = [w for w in (w1, w2, w3, w4, w5, w6, w7) if w]
    evo_summary = build_evolution_summary(
        evolution, evaluation, baseline, adversarial, gan, buffer
    )
    if art_setup:
        evo_summary["art_version"] = art_setup.get("art_version") or adversarial.get("art_version")
    evo_summary["full_evolution_ready"] = summary.get("evolution", {}).get(
        "full_evolution_ready",
        bool(
            evo_summary.get("full_ensemble")
            and evo_summary.get("candidate_trained")
            and evo_summary.get("global_adversarial_gate_passed")
        ),
    )
    return {
        "evolution": evo_summary,
        "evolution_scheduler": summary.get("evolution_scheduler"),
        "model_coverage": summary.get("model_coverage"),
        "human_review_queue_count": summary.get("human_review_queue_count"),
        "full_adversarial_gate": summary.get("full_adversarial_gate"),
        "evaluation_gate": evaluation,
        "production_baseline": baseline,
        "adversarial_hardening": adversarial,
        "gan_generation": gan,
        "training_buffer": buffer,
        "warnings": warnings + (summary.get("warnings") or []),
    }


@router.get("/chronoledger-evidence")
async def dashboard_chrono_evidence() -> Dict[str, Any]:
    chrono, w = _read_json(_evolution_path("chronoledger_evidence.json"))
    return {
        "chronoledger_evidence": build_chrono_summary(chrono),
        "require_human_approval": (chrono or {}).get("require_human_approval_for_chrono", True),
        "warning": w,
    }


@router.get("/latest-events")
async def dashboard_latest_events(limit: int = 20) -> Dict[str, Any]:
    return build_latest_events(limit=limit)


@router.get("/reports")
async def dashboard_reports_list() -> Dict[str, Any]:
    available = {k: v.exists() for k, v in REPORT_FILES.items()}
    return {"reports": available}


@router.get("/reports/{report_id}")
async def dashboard_report_view(report_id: str):
    path = REPORT_FILES.get(report_id)
    if path is None:
        raise HTTPException(status_code=404, detail="unknown_report")
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": "report_missing", "report_id": report_id})
    return FileResponse(path, media_type="application/json", filename=path.name)


async def _run_script(script_name: str, *args: str, timeout: float = 600.0) -> Dict[str, Any]:
    script = WORKSPACE_ROOT / "scripts" / script_name
    if not script.exists():
        raise HTTPException(status_code=404, detail=f"script_not_found:{script_name}")
    cmd = [sys.executable, str(script), *args]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(WORKSPACE_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=504, detail="script_timeout") from None
    return {
        "exit_code": proc.returncode,
        "stdout": stdout.decode("utf-8", errors="replace")[-8000:],
        "stderr": stderr.decode("utf-8", errors="replace")[-4000:],
        "success": proc.returncode == 0,
    }


@router.post("/actions/health-check")
async def action_health_check() -> Dict[str, Any]:
    return {"health": await dashboard_health()}


@router.post("/actions/backend-validation")
async def action_backend_validation() -> Dict[str, Any]:
    sample = {
        "flow_id": f"gui-validation-{int(asyncio.get_running_loop().time() * 1000)}",
        "risk_score": 0.82,
        "risk_label": "HIGH",
        "is_attack": True,
        "attack_family": "operator_validation",
        "src_ip": "192.0.2.10",
        "dst_ip": "198.51.100.20",
        "confidence_band": "HIGH",
        "model_consensus": "gui-action",
    }
    summary_before = build_dashboard_summary()
    try:
        import httpx

        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            response = await client.post("http://127.0.0.1:8000/oracle/process", json=sample)
            body = response.json()
    except Exception as exc:
        return {
            "success": False,
            "backend_status": summary_before["backend_status"],
            "error": str(exc),
            "note": "Lightweight live validation failed; no stack management was attempted.",
        }
    summary_after = build_dashboard_summary()
    return {
        "success": response.status_code in (200, 207),
        "status_code": response.status_code,
        "backend_status": summary_after["backend_status"],
        "oracle_trace_id": body.get("oracle_trace_id"),
        "audit_logged": bool((body.get("audit") or {}).get("logged")),
        "failed_services": body.get("failed_services", []),
        "note": "Lightweight live backend validation; does not start, stop, or kill services.",
    }


@router.post("/actions/evolution-dry-run")
async def action_evolution_dry_run() -> Dict[str, Any]:
    script = WORKSPACE_ROOT / "scripts" / "run_mutantshield_evolution.py"
    if not script.exists():
        evo = await dashboard_evolution()
        return {
            "status": "locked_or_unavailable",
            "safe": True,
            "success": False,
            "reason": "Evolution dry-run script is unavailable in this demonstration build.",
            "production_models_unchanged": True,
            "recommended_action": "Use validated final evolution reports or run offline candidate evaluation manually.",
            "evolution": evo.get("evolution"),
            "promotion_allowed": (evo.get("evolution") or {}).get("promotion_allowed"),
        }
    result = await _run_script(
        "run_mutantshield_evolution.py", "--dry-run", "--max-rows", "5000", timeout=300.0
    )
    evo = await dashboard_evolution()
    return {
        "run": result,
        "evolution": evo.get("evolution"),
        "promotion_allowed": (evo.get("evolution") or {}).get("promotion_allowed"),
    }


@router.post("/actions/qauth-test-token")
async def action_qauth_test_token() -> Dict[str, Any]:
    try:
        import httpx

        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            response = await client.post(
                "http://127.0.0.1:8001/api/v1/tokens/generate",
                json={"metadata": {"source_module": "gui_operator_qauth_test", "purpose": "safe_demo"}},
            )
            body = response.json()
    except Exception as exc:
        return {
            "success": False,
            "locked": False,
            "error": str(exc),
            "note": "QAuthCore test token endpoint could not be reached; no user management was attempted.",
        }
    token = body.get("token") or body.get("access_token") or body.get("qauthcore_token")
    return {
        "success": response.status_code < 400,
        "status_code": response.status_code,
        "token_preview": f"{str(token)[:12]}..." if token else None,
        "keys": sorted(body.keys()) if isinstance(body, dict) else [],
        "note": "Safe test token generation only; no user management or permission changes.",
    }


@router.post("/actions/ghosttunnel-test-transmit")
async def action_ghosttunnel_test_transmit() -> Dict[str, Any]:
    summary = build_dashboard_summary()
    ghost = summary.get("ghosttunnel", {})
    return {
        "success": True,
        "accepted": True,
        "job_id": f"gui-demo-{int(asyncio.get_running_loop().time() * 1000)}",
        "fast_ack_enabled": ghost.get("fast_ack_enabled"),
        "jobs_completed": ghost.get("jobs_completed"),
        "note": "Safe demo transmit acknowledgement only; no persistent tunnel was created.",
    }


@router.post("/actions/chronoledger-chain-verify")
async def action_chronoledger_chain_verify() -> Dict[str, Any]:
    try:
        import httpx

        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            response = await client.get("http://127.0.0.1:8003/chain/verify")
            body = response.json()
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "note": "Chain verify endpoint unavailable; no ledger mutation was attempted.",
        }
    return {
        "success": response.status_code < 500,
        "status_code": response.status_code,
        "chain_status": body.get("status") or body.get("chain_status"),
        "body": body,
        "note": "Read-only chain verification; no ledger mutation was performed.",
    }
