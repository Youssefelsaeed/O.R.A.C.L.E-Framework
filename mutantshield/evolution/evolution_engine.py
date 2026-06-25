"""MutantShield Evolution Engine orchestrator — full ensemble + mandatory adversarial."""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from .candidate_trainer import train_candidates
from .chronoledger_evidence import extract_chronoledger_evidence
from .config import EvolutionConfig, get_config
from .dataset_registry import bootstrap_default_datasets, register_dataset
from .evaluation_gate import run_evaluation_gate
from .full_adversarial import run_full_ensemble_adversarial
from .full_ensemble_trainer import train_full_ensemble
from .gan_adapter import gan_available, generate_synthetic_attacks, load_gan_metadata
from .promotion_manager import promote_candidate
from .reports import write_json
from .synthetic_adapter import run_synthetic_strategy
from .training_buffer import build_training_buffers


def _write_promotion_manifest(
    candidate_dir: Path,
    evaluation: Dict[str, Any],
    coverage: Dict[str, Any],
    adversarial: Dict[str, Any],
    cfg: EvolutionConfig,
) -> None:
    manifest = {
        "generated_at": time.time(),
        "mode": cfg.mode,
        "promotion_allowed": evaluation.get("promotion_allowed", False),
        "promotion_status": evaluation.get("promotion_status"),
        "fair_baseline_reliable": evaluation.get("fair_baseline_reliable"),
        "schema_compatible": evaluation.get("schema_compatible"),
        "global_adversarial_gate_passed": adversarial.get("global_adversarial_gate_passed"),
        "ensemble_promotion_ready": coverage.get("ensemble_promotion_ready", False),
        "human_approval_token_present": bool(cfg.human_approval_token),
        "controlled_promotion_requires": [
            "fair_baseline_reliable",
            "evaluation_passed",
            "global_adversarial_gate_passed",
            "schema_compatible",
            "rollback_available",
            "human_approval_token",
            "full_ensemble_promotion_eligible",
        ],
    }
    write_json(candidate_dir / "promotion_manifest.json", manifest)


class EvolutionEngine:
    def __init__(self, config: Optional[EvolutionConfig] = None) -> None:
        self.cfg = config or get_config()

    def run(
        self,
        *,
        dataset_name: Optional[str] = None,
        dataset_path: Optional[Path] = None,
        label_column: Optional[str] = None,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Any]:
        cfg = self.cfg
        if cfg.mode == "dry-run":
            cfg.dry_run = True
        elif cfg.mode == "candidate-only":
            cfg.dry_run = True
        elif cfg.mode == "controlled-promotion":
            cfg.dry_run = False

        run_id = str(uuid.uuid4())
        t0 = time.time()

        if not cfg.enabled:
            return {"final_status": "FAIL", "error": "evolution_disabled"}

        datasets_used: list = []
        if cfg.use_datasets:
            if dataset_name and dataset_path:
                register_dataset(cfg, dataset_name, dataset_path, label_column=label_column)
            datasets_used = bootstrap_default_datasets(cfg)

        evidence = extract_chronoledger_evidence(cfg) if cfg.use_chronoledger else {"total_events": 0, "events": []}

        gan_meta = load_gan_metadata(cfg)
        gan_status = "skipped_disabled"
        gan_df = pd.DataFrame()
        gan_training_required = True
        if cfg.use_gan:
            gan_df = generate_synthetic_attacks(cfg, n_samples=min(500, cfg.max_samples))
            gan_status = "trained" if gan_available(cfg) else "not_trained"
            gan_training_required = gan_status != "trained"
        else:
            gan_status = "not_trained" if cfg.full_ensemble else "skipped_disabled"

        buffer_summary = build_training_buffers(
            cfg,
            evidence,
            gan_samples=gan_df if not gan_df.empty else None,
            art_samples=None,
            dataset_name=dataset_name,
            dataset_path=dataset_path,
            max_rows=max_rows,
        )

        sup_path = cfg.reports_dir / "training_buffer_supervised.csv"
        supervised_df = pd.read_csv(sup_path) if sup_path.exists() and sup_path.stat().st_size > 0 else pd.DataFrame()
        training_sources = list(buffer_summary.get("source_counts", {}).keys())

        cse_rows_added = 0
        if cfg.include_cse_buffer:
            cse_path = Path(cfg.include_cse_buffer)
            if cse_path.exists() and cse_path.stat().st_size > 0:
                cse_df = pd.read_csv(cse_path, low_memory=False)
                cse_rows_added = len(cse_df)
                supervised_df = pd.concat([supervised_df, cse_df], ignore_index=True) if not supervised_df.empty else cse_df
                training_sources.append("dataset:CSE-CIC-IDS2018")
                buffer_summary["supervised_samples"] = int(buffer_summary.get("supervised_samples", 0)) + cse_rows_added
                counts = dict(buffer_summary.get("source_counts") or {})
                counts["dataset:CSE-CIC-IDS2018"] = counts.get("dataset:CSE-CIC-IDS2018", 0) + cse_rows_added
                buffer_summary["source_counts"] = counts

        synthetic_report = run_synthetic_strategy(
            mode=cfg.synthetic_mode,
            buffer_path=Path(cfg.include_cse_buffer) if cfg.include_cse_buffer else None,
            cfg=cfg,
        )
        if synthetic_report.get("quality_pass") and synthetic_report.get("samples_path"):
            synth_df = pd.read_csv(str(synthetic_report["samples_path"]), low_memory=False)
            supervised_df = pd.concat([supervised_df, synth_df], ignore_index=True) if not supervised_df.empty else synth_df
            training_sources.append(f"synthetic:{cfg.synthetic_mode}")

        if cfg.full_ensemble:
            candidate_result = train_full_ensemble(cfg, supervised_df, training_sources)
            coverage_report = candidate_result.get("coverage_report") or {}
        else:
            candidate_result = train_candidates(cfg, supervised_df, training_sources)
            coverage_report = {}

        candidate_dir = Path(candidate_result.get("candidate_dir", ""))

        adversarial_skipped = cfg.skip_adversarial
        adversarial_report = run_full_ensemble_adversarial(
            cfg,
            candidate_result,
            coverage_report,
            apply_training=False,
            skipped=adversarial_skipped,
        )
        for m in coverage_report.get("models", []):
            name = m.get("model_name")
            pm = (adversarial_report.get("per_model") or {}).get(name, {})
            if pm:
                m["adversarial_evaluated"] = pm.get("status") not in ("skipped", "not_trained", "no_candidate_artifact")
                m["adversarial_training_applied"] = bool(
                    cfg.adversarial_train and m.get("candidate_trained")
                )
        from .model_coverage import build_coverage_report

        build_coverage_report(cfg, coverage_report.get("models", []), candidate_dir=candidate_dir)
        adversarial_before = {
            "clean_accuracy": adversarial_report.get("clean_accuracy"),
            "adversarial_accuracy": adversarial_report.get("adversarial_accuracy"),
            "robustness_drop": adversarial_report.get("robustness_drop"),
        }

        adversarial_training_enabled = False
        adversarial_samples_used = 0
        adversarial_after: Dict[str, Any] = {}
        robustness_improved = False

        do_adv_train = cfg.adversarial_train and not adversarial_skipped and cfg.mode in (
            "candidate-only",
            "controlled-promotion",
        )
        if do_adv_train:
            art_samples = adversarial_report.get("adversarial_samples")
            if isinstance(art_samples, pd.DataFrame) and not art_samples.empty:
                adversarial_training_enabled = True
                adversarial_samples_used = len(art_samples)
                buffer_summary = build_training_buffers(
                    cfg,
                    evidence,
                    gan_samples=gan_df if not gan_df.empty else None,
                    art_samples=art_samples,
                    dataset_name=dataset_name,
                    dataset_path=dataset_path,
                    max_rows=max_rows,
                )
                if sup_path.exists() and sup_path.stat().st_size > 0:
                    supervised_df = pd.read_csv(sup_path)
                    if cfg.full_ensemble:
                        candidate_result = train_full_ensemble(
                            cfg,
                            supervised_df,
                            training_sources + ["art"],
                            candidate_id=candidate_result.get("candidate_id"),
                        )
                        coverage_report = candidate_result.get("coverage_report") or {}
                    else:
                        candidate_result = train_candidates(cfg, supervised_df, training_sources + ["art"])

                adversarial_report = run_full_ensemble_adversarial(
                    cfg,
                    candidate_result,
                    coverage_report,
                    apply_training=True,
                    skipped=False,
                )
                for m in coverage_report.get("models", []):
                    name = m.get("model_name")
                    pm = (adversarial_report.get("per_model") or {}).get(name, {})
                    if pm:
                        m["adversarial_evaluated"] = pm.get("status") not in (
                            "skipped",
                            "not_trained",
                            "no_candidate_artifact",
                        )
                        m["adversarial_training_applied"] = bool(
                            cfg.adversarial_train and m.get("candidate_trained")
                        )
                build_coverage_report(cfg, coverage_report.get("models", []), candidate_dir=candidate_dir)
                adversarial_after = {
                    "clean_accuracy": adversarial_report.get("clean_accuracy"),
                    "adversarial_accuracy": adversarial_report.get("adversarial_accuracy"),
                    "robustness_drop": adversarial_report.get("robustness_drop"),
                }
                before_drop = float(adversarial_before.get("robustness_drop") or 0)
                after_drop = float(adversarial_after.get("robustness_drop") or 0)
                robustness_improved = after_drop < before_drop

        evaluation = run_evaluation_gate(
            cfg,
            candidate_result,
            adversarial_report,
            coverage_report=coverage_report,
        )
        if candidate_dir.exists():
            write_json(candidate_dir / "evaluation_report.json", evaluation)
            _write_promotion_manifest(candidate_dir, evaluation, coverage_report, adversarial_report, cfg)

        promotion = {"promoted": False, "simulated": cfg.dry_run}
        if candidate_result.get("success") and cfg.mode == "controlled-promotion":
            promotion = promote_candidate(
                cfg,
                candidate_dir,
                evaluation,
                candidate_result.get("metadata", {}),
            )
        elif candidate_result.get("success"):
            promotion = promote_candidate(
                cfg,
                candidate_dir,
                evaluation,
                candidate_result.get("metadata", {}),
            )

        xgb_adv = (adversarial_report.get("per_model") or {}).get("XGBoost", {})
        art_status = "skipped" if adversarial_skipped else (
            "available" if adversarial_report.get("art_available") and not xgb_adv.get("fallback_used") else (
                "fallback" if xgb_adv.get("fallback_used") else "evaluated"
            )
        )

        if not candidate_result.get("success"):
            final_status = "FAIL"
        elif cfg.dry_run and candidate_result.get("success"):
            final_status = "PASS_DRY_RUN"
        elif promotion.get("promoted"):
            final_status = "PASS"
        elif evaluation.get("passed"):
            final_status = "PASS"
        else:
            final_status = "PASS_DRY_RUN" if cfg.dry_run else "FAIL"

        report = {
            "run_id": run_id,
            "timestamp": time.time(),
            "duration_s": round(time.time() - t0, 2),
            "mode": cfg.mode,
            "dry_run": cfg.dry_run,
            "full_ensemble": cfg.full_ensemble,
            "datasets_used": [d.get("dataset_name") for d in datasets_used],
            "chronoledger_evidence_count": evidence.get("total_events", 0),
            "supervised_buffer_count": buffer_summary.get("supervised_samples", 0),
            "cse_buffer_rows_added": cse_rows_added,
            "synthetic_mode": cfg.synthetic_mode,
            "synthetic_status": synthetic_report.get("status"),
            "synthetic_quality_pass": synthetic_report.get("quality_pass", False),
            "anomaly_buffer_count": buffer_summary.get("anomaly_samples", 0),
            "unverified_buffer_count": buffer_summary.get("unverified_samples", 0),
            "gan_status": gan_status,
            "gan_training_required": gan_training_required,
            "art_status": art_status,
            "art_available": adversarial_report.get("art_available", False),
            "art_source": adversarial_report.get("art_source"),
            "attacks_run": xgb_adv.get("attacks_run", adversarial_report.get("attacks_run", [])),
            "adversarial_accuracy": adversarial_report.get("adversarial_accuracy"),
            "robustness_drop": adversarial_report.get("robustness_drop"),
            "global_adversarial_gate_passed": adversarial_report.get("global_adversarial_gate_passed"),
            "adversarial_skipped": adversarial_skipped,
            "adversarial_training_enabled": adversarial_training_enabled,
            "adversarial_samples_used": adversarial_samples_used,
            "clean_before": adversarial_before.get("clean_accuracy"),
            "adversarial_before": adversarial_before.get("adversarial_accuracy"),
            "clean_after": adversarial_after.get("clean_accuracy"),
            "adversarial_after": adversarial_after.get("adversarial_accuracy"),
            "robustness_improved": robustness_improved,
            "fair_baseline_reliable": evaluation.get("fair_baseline_reliable"),
            "model_coverage": coverage_report,
            "models_trained_count": coverage_report.get("models_trained_count", 0),
            "ensemble_promotion_ready": coverage_report.get("ensemble_promotion_ready", False),
            "candidate_id": candidate_result.get("candidate_id"),
            "candidate_trained": candidate_result.get("success", False),
            "evaluation_passed": evaluation.get("passed", False),
            "promotion_allowed": evaluation.get("promotion_allowed", False),
            "promotion_status": evaluation.get("promotion_status", "unknown"),
            "baseline_quality_warning": evaluation.get("baseline_quality_warning", False),
            "promoted": promotion.get("promoted", False),
            "promotion_simulated": promotion.get("simulated", cfg.dry_run),
            "rollback_available": promotion.get("rollback_available", False),
            "final_status": final_status,
            "evaluation_reasons": evaluation.get("reasons", []),
        }
        write_json(cfg.reports_dir / "evolution_run_report.json", report)
        return report
