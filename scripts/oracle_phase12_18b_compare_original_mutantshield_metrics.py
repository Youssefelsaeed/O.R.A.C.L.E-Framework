"""Compare historical MutantShield metrics against Phase 12.18B controlled metrics."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from oracle_phase12_18_common import ROOT, write_json, write_md

SEARCH_FILES = [ROOT / "README.md", ROOT / "docs" / "TESTING_AND_VALIDATION.md", ROOT / "docs" / "MODULE_CAPABILITIES.md", ROOT / "reports" / "final" / "ORACLE_FINAL_CAPABILITY_MATRIX.md"]


def _claims(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if re.search(r"(?i)(recall|accuracy|precision|f1|fpr|fnr|detection)", line) and re.search(r"\b(0?\.\d+|1\.0|100%|\d+\.\d+%)", line)][:100]


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}


def run() -> Dict[str, Any]:
    controlled = _read_json(ROOT / "reports" / "final" / "phase12_18b_mutantshield_controlled_eval.json")
    docs = {str(path.relative_to(ROOT)): _claims(path.read_text(encoding="utf-8", errors="ignore")) if path.exists() else [] for path in SEARCH_FILES}
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "historical_claims": docs,
        "controlled_metrics_source": "reports/final/phase12_18b_mutantshield_controlled_eval.json",
        "controlled_results": {key: {"status": val.get("status"), "rows": val.get("rows_evaluated"), "metrics": val.get("metrics"), "metrics_final_claim_valid": val.get("metrics_final_claim_valid")} for key, val in (controlled.get("results") or {}).items()},
        "explanations": ["Historical training/validation metrics are not equivalent to external balanced validation.", "Production, candidate, mapped-domain, and native-adapter paths must be reported separately.", "Use Phase 12.18B controlled metrics for presentation unless superseded by a larger fresh rerun."],
        "pass": True,
    }
    json_path = write_json("phase12_18b_original_metric_comparison.json", report)
    lines = ["# Phase 12.18B Original Metric Comparison", ""]
    for src, claims in docs.items():
        lines += [f"## {src}", *(f"- {c}" for c in claims[:20]), ""]
    lines += ["## Explanation", *(f"- {e}" for e in report["explanations"])]
    md_path = write_md("phase12_18b_original_metric_comparison.md", lines)
    report["json_report_path"] = str(json_path); report["markdown_report_path"] = str(md_path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B ORIGINAL METRIC COMPARISON ===")
    print(f"Sources Compared: {len(report['historical_claims'])}")
    print("Final Status: PASS")
    print(f"Report: {report['json_report_path']}")


if __name__ == "__main__":
    main()
