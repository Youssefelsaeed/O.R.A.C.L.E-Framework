"""Generate final Phase 12.18B detection verdict."""
from __future__ import annotations

import json
import time
from typing import Any, Dict

from oracle_phase12_17_common import model_hashes
from oracle_phase12_18_common import ROOT, write_json, write_md


def _read(name: str) -> Dict[str, Any]:
    try:
        data = json.loads((ROOT / "reports" / "final" / name).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}


def run() -> Dict[str, Any]:
    sets = _read("phase12_18b_eval_set_summary.json")
    standalone = _read("phase12_18b_mutantshield_controlled_eval.json")
    full = _read("phase12_18b_full_stack_controlled_eval.json")
    runtime = _read("phase12_18b_runtime_reset_report.json")
    comparison = _read("phase12_18b_original_metric_comparison.json")
    keys = sorted(set((standalone.get("results") or {}).keys()) | set((full.get("results") or {}).keys()))
    metrics = {key: {"standalone": (standalone.get("results") or {}).get(key, {}).get("metrics"), "full_stack": (full.get("results") or {}).get(key, {}).get("detection_metrics"), "final_claim_valid": (standalone.get("results") or {}).get(key, {}).get("metrics_final_claim_valid")} for key in keys}
    proof = []
    for item in (full.get("results") or {}).values():
        proof.extend((item.get("proof_records") or [])[:2])
    preserved = bool(proof) and all(r.get("fields_preserved") for r in proof)
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "did_generate_flows_from_datasets": bool(sets.get("datasets")),
        "dataset_generation_method": "Balanced CSV eval sets from local dataset rows with original_label, y_true, dataset_source, attack_family, and row_origin_file.",
        "tested_mutantshield_alone": bool(standalone.get("results")),
        "tested_full_oracle_stack": bool(full.get("results")),
        "oracle_core_uses_real_mutantshield_output": preserved,
        "proof_records_sample": proof[:10],
        "trustworthy_final_metrics": metrics,
        "presentation_metrics": "Use only Phase 12.18B per-dataset/path metrics with final_claim_valid=true; do not use unsupported banner metrics.",
        "unsupported_or_outdated_metrics": comparison.get("historical_claims", {}),
        "confident_detection": ["Report CIC/CSE-style production FusionEngine only for measured balanced paths.", "Report DoHBrw through native adapter when measured."],
        "not_confident_detection": ["Paths with weak recall/F1 in controlled evaluation.", "UNSW as native production claim because it is mapped validation.", "CSE repair candidate when no candidate bundle is present."],
        "learn_adapt_capability": ["Candidate-only XGBoost/AutoEncoder retraining.", "CSE repair candidates when available.", "DoHBrw native adapter candidates.", "LSTM/GNN retraining after contracts pass."],
        "runtime_current_code_verified": bool(runtime.get("pass")),
        "models_final_hashes_present": bool(model_hashes()),
    }
    report["final_status"] = "ORACLE_DETECTION_VERIFIED" if report["runtime_current_code_verified"] and preserved else "NOT_READY"
    report["pass"] = report["final_status"] == "ORACLE_DETECTION_VERIFIED"
    json_path = write_json("ORACLE_FINAL_DETECTION_VERDICT.json", report)
    lines = ["# ORACLE Final Detection Verdict", "", f"Final Status: `{report['final_status']}`", "", f"- Did we generate flows from datasets? `{report['did_generate_flows_from_datasets']}`", f"- Did we test MutantShield alone? `{report['tested_mutantshield_alone']}`", f"- Did we test full ORACLE stack? `{report['tested_full_oracle_stack']}`", f"- Does Oracle Core use real MutantShield output? `{report['oracle_core_uses_real_mutantshield_output']}`", "", "## Presentation Metrics", report["presentation_metrics"], "", "## Remaining Limits", *(f"- {x}" for x in report["not_confident_detection"])]
    md_path = write_md("ORACLE_FINAL_DETECTION_VERDICT.md", lines)
    report["json_report_path"] = str(json_path); report["markdown_report_path"] = str(md_path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B FINAL DETECTION VERDICT ===")
    print(f"MutantShield Alone Tested: {report['tested_mutantshield_alone']}")
    print(f"Full Stack Tested: {report['tested_full_oracle_stack']}")
    print(f"Oracle Preserved Detector Output: {report['oracle_core_uses_real_mutantshield_output']}")
    print(f"Final Status: {report['final_status']}")
    print(f"Report: {report['json_report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
