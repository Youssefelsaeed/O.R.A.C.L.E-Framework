"""Build balanced Phase 12.18B dataset evaluation CSVs."""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from oracle_phase12_18_common import DATASETS, detect_label_column, discover_dataset_files, import_pandas, normalize_binary_label, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "final" / "phase12_18b_eval_sets"
TARGET_BENIGN = 500
TARGET_ATTACK = 500
SEED = 1218


def _safe_name(dataset: str) -> str:
    return dataset.replace("/", "_").replace(" ", "_")


def _read_candidates(dataset_name: str, per_file_rows: int = 10000) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    pd, err = import_pandas()
    if pd is None:
        raise RuntimeError(f"pandas_unavailable:{err}")
    benign: List[Dict[str, Any]] = []
    attack: List[Dict[str, Any]] = []
    files_read: List[str] = []
    labels = Counter()
    label_columns = Counter()
    errors: List[Dict[str, str]] = []
    for path in discover_dataset_files(dataset_name):
        if len(benign) >= TARGET_BENIGN and len(attack) >= TARGET_ATTACK:
            break
        try:
            df = pd.read_parquet(path) if path.suffix.lower() == ".parquet" else pd.read_csv(path, low_memory=False, nrows=per_file_rows)
            if path.suffix.lower() == ".parquet" and len(df) > per_file_rows:
                df = df.sample(n=per_file_rows, random_state=SEED)
            label_col = detect_label_column(df.columns, DATASETS[dataset_name].get("label_hint") or [])
            if not label_col:
                continue
            files_read.append(str(path))
            label_columns[str(label_col)] += 1
            for _, row in df.iterrows():
                y = normalize_binary_label(row[label_col])
                original = str(row[label_col])
                labels[original] += 1
                rec = row.to_dict()
                rec.update(
                    {
                        "original_label": original,
                        "y_true": y,
                        "dataset_source": dataset_name,
                        "attack_family": "benign" if y == 0 else original,
                        "row_origin_file": str(path),
                    }
                )
                if y == 0 and len(benign) < TARGET_BENIGN:
                    benign.append(rec)
                elif y == 1 and len(attack) < TARGET_ATTACK:
                    attack.append(rec)
                if len(benign) >= TARGET_BENIGN and len(attack) >= TARGET_ATTACK:
                    break
        except Exception as exc:
            errors.append({"file": str(path), "error": f"{type(exc).__name__}:{exc}"})
    meta = {"files_read": files_read, "label_columns_seen": dict(label_columns), "raw_label_distribution_scanned": dict(labels), "read_errors": errors[:20]}
    return benign, attack, meta


def _build_one(dataset_name: str) -> Dict[str, Any]:
    pd, err = import_pandas()
    if pd is None:
        return {"dataset": dataset_name, "status": "ERROR", "error": f"pandas_unavailable:{err}"}
    benign, attack, meta = _read_candidates(dataset_name)
    rows = benign + attack
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{_safe_name(dataset_name)}.csv"
    if rows:
        df = pd.DataFrame(rows).sample(frac=1.0, random_state=SEED).reset_index(drop=True)
        df.to_csv(out_path, index=False)
    counts = {"benign": len(benign), "attack": len(attack)}
    status = "pass" if counts["benign"] > 0 and counts["attack"] > 0 else "limited_unbalanced"
    return {
        "dataset": dataset_name,
        "status": status,
        "output_csv": str(out_path),
        "target": {"benign": TARGET_BENIGN, "attack": TARGET_ATTACK},
        "actual_distribution": counts,
        "balance_note": "target_met" if counts["benign"] >= TARGET_BENIGN and counts["attack"] >= TARGET_ATTACK else "insufficient_labels_for_500_500",
        **meta,
    }


def run() -> Dict[str, Any]:
    results = {name: _build_one(name) for name in DATASETS}
    report: Dict[str, Any] = {"generated_at": time.time(), "output_dir": str(OUT_DIR), "fixed_seed": SEED, "datasets": results}
    report["pass"] = all(item.get("status") in {"pass", "limited_unbalanced"} for item in results.values())
    path = write_json("phase12_18b_eval_set_summary.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B BALANCED EVAL SETS ===")
    for name, item in report["datasets"].items():
        dist = item.get("actual_distribution", {})
        print(f"{name}: {item.get('status')} benign={dist.get('benign')} attack={dist.get('attack')}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
