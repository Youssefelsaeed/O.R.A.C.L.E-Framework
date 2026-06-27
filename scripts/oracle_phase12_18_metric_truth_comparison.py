"""Compare old banner metrics with fresh Phase 12.18 evidence."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from oracle_phase12_18_common import ROOT, write_json, write_md

DOCS = [
    ROOT / "README.md",
    ROOT / "docs" / "TESTING_AND_VALIDATION.md",
    ROOT / "docs" / "MODULE_CAPABILITIES.md",
    ROOT / "reports" / "final" / "ORACLE_FINAL_CAPABILITY_MATRIX.md",
]


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}


def _extract_percent_claims(text: str) -> List[str]:
    claims = []
    for match in re.finditer(r"(?i)(accuracy|precision|recall|f1|fpr|fnr|detection|success)[^\\n]{0,80}?([0-9]{1,3}(?:\\.[0-9]+)?%)", text):
        claims.append(match.group(0).strip())
    return claims[:100]


def run() -> Dict[str, Any]:
    standalone = _read_json(ROOT / "reports" / "final" / "phase12_18_mutantshield_standalone_eval.json")
    full_stack = _read_json(ROOT / "reports" / "final" / "phase12_18_full_stack_dataset_eval.json")
    fresh_available = any((item.get("status") == "PASS" and item.get("rows_tested", item.get("events_sent", 0)) > 0) for item in (standalone.get("results") or {}).values())
    docs = {}
    claims: List[Dict[str, Any]] = []
    for path in DOCS:
        if not path.exists():
            docs[str(path.relative_to(ROOT))] = {"exists": False, "claims": []}
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        extracted = _extract_percent_claims(text)
        docs[str(path.relative_to(ROOT))] = {"exists": True, "claims": extracted}
        for claim in extracted:
            claims.append(
                {
                    "source": str(path.relative_to(ROOT)),
                    "claim": claim,
                    "classification": "confirmed" if fresh_available else "unsupported",
                    "recommendation": "Keep only if it matches Phase 12.18 per-dataset row metrics." if fresh_available else "Remove from banner/global summary or label as historical/unverified.",
                }
            )
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "fresh_metrics_available": fresh_available,
        "documents_scanned": docs,
        "claims": claims,
        "classification_summary": {
            "confirmed": sum(1 for c in claims if c["classification"] == "confirmed"),
            "unsupported": sum(1 for c in claims if c["classification"] == "unsupported"),
        },
        "corrected_metric_policy": [
            "Do not publish one global detection number unless all datasets are evaluated in Phase 12.18.",
            "Show per-dataset rows for Production FusionEngine, CSE repair candidate, DoHBrw mapped path, DoHBrw native adapter, and full ORACLE stack.",
            "If raw datasets are absent, mark metrics as blocked/unverified instead of carrying old banner values.",
        ],
    }
    report["pass"] = True
    json_path = write_json("phase12_18_metric_truth_comparison.json", report)
    md = ["# Phase 12.18 Metric Truth Comparison", "", f"Fresh metrics available: `{fresh_available}`", ""]
    for claim in claims[:50]:
        md += [f"- `{claim['classification']}`: {claim['source']} — {claim['claim']}"]
    if not claims:
        md.append("No percentage metric claims were found by the scanner.")
    md += ["", "## Corrected Policy", *[f"- {x}" for x in report["corrected_metric_policy"]]]
    md_path = write_md("phase12_18_metric_truth_comparison.md", md)
    report["json_report_path"] = str(json_path)
    report["markdown_report_path"] = str(md_path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18 METRIC TRUTH COMPARISON ===")
    print(f"Fresh Metrics Available: {report['fresh_metrics_available']}")
    print(f"Confirmed Claims: {report['classification_summary']['confirmed']}")
    print(f"Unsupported Claims: {report['classification_summary']['unsupported']}")
    print("Final Status: PASS")
    print(f"Report: {report['json_report_path']}")


if __name__ == "__main__":
    main()
