"""Synthetic data strategy for candidate-only evolution buffers."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import EvolutionConfig, get_config
from .gan_adapter import gan_available, generate_synthetic_attacks, load_gan_metadata
from .reports import write_json

REPORT_NAME = "synthetic_data_strategy_report.json"


def _validate_samples(samples: pd.DataFrame, reference: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
    checks: Dict[str, bool] = {}
    reasons: List[str] = []
    if samples.empty:
        return {"quality_pass": False, "checks": {"non_empty": False}, "reasons": ["no_samples"]}

    checks["feature_count"] = all(c in samples.columns for c in feature_cols) and len(feature_cols) == 78
    checks["no_nan_inf"] = bool(np.isfinite(samples[feature_cols].to_numpy(dtype=float)).all())

    ref = reference[feature_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    syn = samples[feature_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    low = ref.quantile(0.001)
    high = ref.quantile(0.999)
    within = ((syn >= low) & (syn <= high)).mean().mean()
    checks["range_within_percentiles"] = bool(within >= 0.95)

    label_values = set(str(v).lower() for v in samples.get("label", pd.Series(["synthetic_attack"])).unique())
    checks["label_distribution_valid"] = bool(label_values)

    duplicate_rate = float(syn.duplicated().mean()) if len(syn) else 1.0
    checks["no_exact_duplicate_spike"] = duplicate_rate <= 0.05

    # Lightweight outlier check: average z-score magnitude should stay bounded.
    std = ref.std().replace(0, 1.0)
    z = ((syn - ref.mean()) / std).abs().replace([np.inf, -np.inf], 0.0).fillna(0.0)
    checks["outlier_check_not_extreme"] = float(z.mean().mean()) <= 6.0

    for key, ok in checks.items():
        if not ok:
            reasons.append(key)
    return {
        "quality_pass": all(checks.values()),
        "checks": checks,
        "reasons": reasons,
        "duplicate_rate": round(duplicate_rate, 4),
        "range_within_percentiles_ratio": round(float(within), 4),
    }


def _sdv_available() -> Tuple[bool, Optional[str]]:
    try:
        import sdv  # type: ignore  # noqa: F401

        return True, None
    except Exception as exc:
        return False, str(exc)


def run_synthetic_strategy(
    *,
    mode: str = "disabled",
    buffer_path: Optional[Path] = None,
    n_samples: int = 500,
    cfg: Optional[EvolutionConfig] = None,
) -> Dict[str, Any]:
    cfg = cfg or get_config()
    mode = str(mode or "disabled").strip()
    report_path = cfg.reports_dir / REPORT_NAME
    base: Dict[str, Any] = {
        "generated_at": time.time(),
        "mode": mode,
        "status": "disabled",
        "samples_generated": 0,
        "samples_added_to_candidate_buffer": 0,
        "quality_pass": False,
        "synthetic_is_ground_truth": False,
    }

    if mode == "disabled":
        base["status"] = "disabled"
        base["recommendation"] = "Synthetic data disabled by default for Phase 9 safety"
        write_json(report_path, base)
        return base

    if buffer_path is None or not buffer_path.exists() or buffer_path.stat().st_size == 0:
        base.update({"status": "skipped", "reason": "candidate_buffer_missing"})
        write_json(report_path, base)
        return base

    reference = pd.read_csv(buffer_path, low_memory=False)
    feature_cols = [
        c
        for c in reference.columns
        if c
        not in {
            "label",
            "is_attack",
            "label_trust",
            "source",
            "source_file",
            "source_dataset",
            "original_label",
            "feature_mapping_quality",
            "missing_mapped_features",
        }
        and pd.api.types.is_numeric_dtype(reference[c])
    ]

    if mode == "existing_gan":
        meta = load_gan_metadata(cfg)
        if not gan_available(cfg):
            base.update({"status": "not_trained", "gan_metadata": meta})
            write_json(report_path, base)
            return base
        samples = generate_synthetic_attacks(cfg, n_samples=n_samples)
        if samples.empty:
            base.update({"status": "not_trained", "gan_metadata": meta})
            write_json(report_path, base)
            return base
        samples = samples.reindex(columns=feature_cols, fill_value=0.0)
        samples["label"] = "synthetic_attack"
        samples["is_attack"] = 1
        samples["label_trust"] = "synthetic"
        samples["source"] = "synthetic:existing_gan"
        quality = _validate_samples(samples, reference, feature_cols)
        base.update({"status": "available", "samples_generated": len(samples), **quality})
        if base.get("quality_pass"):
            samples_path = cfg.reports_dir / "synthetic_candidate_samples.csv"
            samples.to_csv(samples_path, index=False)
            base["samples_path"] = str(samples_path)
            base["samples_added_to_candidate_buffer"] = len(samples)
        write_json(report_path, base)
        return base

    if mode == "tabular_synthetic":
        available, error = _sdv_available()
        if not available:
            base.update(
                {
                    "status": "skipped_dependency_missing",
                    "dependency": "sdv",
                    "error": error,
                    "install_recommendation": "pip install sdv",
                }
            )
            write_json(report_path, base)
            return base
        try:
            attack_df = reference[reference["is_attack"].astype(int) == 1].copy()
            if len(attack_df) < 50:
                base.update({"status": "skipped_insufficient_attack_rows", "attack_rows": len(attack_df)})
                write_json(report_path, base)
                return base
            try:
                from sdv.metadata import SingleTableMetadata  # type: ignore
                from sdv.single_table import CTGANSynthesizer  # type: ignore

                train_df = attack_df[feature_cols].sample(n=min(len(attack_df), 1000), random_state=42)
                metadata = SingleTableMetadata()
                metadata.detect_from_dataframe(train_df)
                synth = CTGANSynthesizer(metadata, epochs=10, verbose=False)
                synth.fit(train_df)
                samples = synth.sample(num_rows=min(n_samples, len(train_df)))
            except Exception:
                from sdv.tabular import CTGAN  # type: ignore

                train_df = attack_df[feature_cols].sample(n=min(len(attack_df), 1000), random_state=42)
                synth = CTGAN(epochs=10, verbose=False)
                synth.fit(train_df)
                samples = synth.sample(min(n_samples, len(train_df)))
            samples = samples.reindex(columns=feature_cols, fill_value=0.0)
            for col in feature_cols:
                lo = float(reference[col].quantile(0.001))
                hi = float(reference[col].quantile(0.999))
                samples[col] = pd.to_numeric(samples[col], errors="coerce").fillna(0.0).clip(lo, hi)
            samples["label"] = "synthetic_attack"
            samples["is_attack"] = 1
            samples["label_trust"] = "synthetic"
            samples["source"] = "synthetic:tabular"
            quality = _validate_samples(samples, reference, feature_cols)
            base.update({"status": "generated", "samples_generated": len(samples), **quality})
            if base.get("quality_pass"):
                samples_path = cfg.reports_dir / "synthetic_candidate_samples.csv"
                samples.to_csv(samples_path, index=False)
                base["samples_path"] = str(samples_path)
                base["samples_added_to_candidate_buffer"] = len(samples)
            write_json(report_path, base)
            return base
        except Exception as exc:
            base.update({"status": "error", "error": str(exc)})
            write_json(report_path, base)
            return base

    base.update({"status": "error", "reason": f"unknown_mode:{mode}"})
    write_json(report_path, base)
    return base
