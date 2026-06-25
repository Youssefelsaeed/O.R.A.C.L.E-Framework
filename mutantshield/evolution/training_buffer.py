"""Safe training buffer builder — trusted datasets vs unverified ChronoLedger evidence."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .config import EvolutionConfig
from .dataset_registry import KNOWN_DATASETS, load_dataset_sample, list_datasets
from .reports import write_json


def _is_benign_label(label: str) -> bool:
    s = str(label).strip().lower()
    return s in ("benign", "normal", "0", "0.0") or "benign" in s or "normal" in s


def build_training_buffers(
    cfg: EvolutionConfig,
    evidence_report: Dict[str, Any],
    gan_samples: Optional[pd.DataFrame] = None,
    art_samples: Optional[pd.DataFrame] = None,
    dataset_name: Optional[str] = None,
    dataset_path: Optional[Path] = None,
    max_rows: Optional[int] = None,
) -> Dict[str, Any]:
    max_rows = max_rows or cfg.max_samples
    supervised_rows: List[Dict[str, Any]] = []
    anomaly_rows: List[Dict[str, Any]] = []
    unverified_rows: List[Dict[str, Any]] = []
    source_counts: Dict[str, int] = {}

    # 1. Official datasets (trusted labels)
    if cfg.use_datasets:
        datasets = list_datasets(cfg)
        if dataset_name and dataset_path:
            ds_list = [{"dataset_name": dataset_name, "dataset_path": str(dataset_path), "label_column": "Label"}]
        else:
            ds_list = datasets

        for ds in ds_list:
            name = ds.get("dataset_name", "unknown")
            path = Path(ds.get("dataset_path", ""))
            label_col = ds.get("label_column") or KNOWN_DATASETS.get(name, {}).get("label_column", "Label")
            df = load_dataset_sample(name, path, label_col, max_rows=max_rows)
            if df is None or df.empty:
                continue
            df.columns = [str(c).strip() for c in df.columns]
            label_col = label_col.strip()
            source_counts[f"dataset:{name}"] = source_counts.get(f"dataset:{name}", 0) + len(df)
            feature_cols = [c for c in df.columns if c != label_col and pd.api.types.is_numeric_dtype(df[c])]
            for _, row in df.iterrows():
                label_val = row.get(label_col, "unknown")
                rec = {}
                for c in feature_cols:
                    v = row[c]
                    if pd.isna(v) or (isinstance(v, float) and (np.isinf(v) or abs(v) > 1e15)):
                        rec[c] = 0.0
                    else:
                        rec[c] = float(v)
                rec["label"] = str(label_val)
                rec["is_attack"] = 0 if _is_benign_label(str(label_val)) else 1
                rec["label_trust"] = "verified"
                rec["source"] = f"dataset:{name}"
                supervised_rows.append(rec)

    # 2. GAN synthetic (trusted as synthetic attack)
    if gan_samples is not None and not gan_samples.empty:
        source_counts["gan_synthetic"] = len(gan_samples)
        for _, row in gan_samples.iterrows():
            rec = row.to_dict()
            rec["label"] = "SYNTHETIC_ATTACK"
            rec["is_attack"] = 1
            rec["label_trust"] = "synthetic"
            rec["source"] = "gan"
            supervised_rows.append(rec)

    # 3. ART adversarial samples
    if art_samples is not None and not art_samples.empty:
        source_counts["art_adversarial"] = len(art_samples)
        for _, row in art_samples.iterrows():
            rec = row.to_dict()
            rec.setdefault("label", "ADVERSARIAL")
            rec.setdefault("is_attack", 1)
            rec.setdefault("label_trust", "adversarial")
            rec.setdefault("source", "art")
            supervised_rows.append(rec)

    # 4. ChronoLedger evidence (untrusted unless human_reviewed)
    for ev in evidence_report.get("events", []):
        bucket = ev.get("evidence_bucket", "outlier_candidate")
        trust = ev.get("label_trust", "unverified")
        base = {
            "risk_score": float(ev.get("risk_score", 0) or 0),
            "is_attack_reported": int(bool(ev.get("is_attack", False))),
            "risk_label": ev.get("risk_label"),
            "attack_family": ev.get("attack_family"),
            "flow_id": ev.get("flow_id"),
            "oracle_trace_id": ev.get("oracle_trace_id"),
            "evidence_bucket": bucket,
            "label_trust": trust,
            "source": "chronoledger",
        }
        source_counts["chronoledger"] = source_counts.get("chronoledger", 0) + 1

        if trust == "verified" and bucket in ("high_confidence_attack", "high_confidence_benign"):
            rec = dict(base)
            rec["label"] = "attack" if bucket == "high_confidence_attack" else "benign"
            rec["is_attack"] = 1 if bucket == "high_confidence_attack" else 0
            supervised_rows.append(rec)
        elif bucket in ("false_positive_candidate", "false_negative_candidate", "human_review_required"):
            unverified_rows.append(base)
        else:
            anomaly_rows.append(base)

    supervised_df = pd.DataFrame(supervised_rows) if supervised_rows else pd.DataFrame()
    anomaly_df = pd.DataFrame(anomaly_rows) if anomaly_rows else pd.DataFrame()

    sup_path = cfg.reports_dir / "training_buffer_supervised.csv"
    ano_path = cfg.reports_dir / "training_buffer_anomaly.csv"
    unv_path = cfg.reports_dir / "training_buffer_unverified.json"

    if not supervised_df.empty:
        supervised_df.to_csv(sup_path, index=False)
    else:
        sup_path.write_text("", encoding="utf-8")
    if not anomaly_df.empty:
        anomaly_df.to_csv(ano_path, index=False)
    else:
        ano_path.write_text("", encoding="utf-8")
    write_json(unv_path, {"samples": unverified_rows, "count": len(unverified_rows)})

    attack_samples = int(supervised_df["is_attack"].sum()) if not supervised_df.empty and "is_attack" in supervised_df.columns else 0
    benign_samples = len(supervised_df) - attack_samples if not supervised_df.empty else 0

    summary = {
        "generated_at": time.time(),
        "supervised_samples": len(supervised_df),
        "anomaly_samples": len(anomaly_df),
        "unverified_samples": len(unverified_rows),
        "attack_samples": attack_samples,
        "benign_samples": benign_samples,
        "source_counts": source_counts,
        "schema_status": "ok" if len(supervised_df) >= cfg.min_samples else "insufficient_samples",
        "supervised_path": str(sup_path),
        "anomaly_path": str(ano_path),
        "unverified_path": str(unv_path),
    }
    write_json(cfg.reports_dir / "training_buffer_summary.json", summary)
    return summary
