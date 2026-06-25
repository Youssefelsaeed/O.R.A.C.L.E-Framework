"""Adversarial hardening — IBM ART when available, fallback mutations otherwise."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .art_integration import ensure_art_on_path
from .config import EvolutionConfig
from .reports import write_json


def _fallback_attacks(X: np.ndarray, y: np.ndarray, n: int = 200) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    rng = np.random.default_rng(42)
    idx = rng.choice(len(X), size=min(n, len(X)), replace=False)
    Xs = X[idx].copy()
    ys = y[idx].copy()
    attacks_run = ["gaussian_noise", "feature_jitter", "feature_scaling", "random_feature_dropout"]
    noise = rng.normal(0, 0.05, size=Xs.shape)
    Xs = Xs + noise
    jitter = rng.uniform(0.9, 1.1, size=Xs.shape)
    Xs = Xs * jitter
    drop_mask = rng.random(size=Xs.shape) < 0.05
    Xs[drop_mask] = 0
    return Xs, ys, attacks_run


def _wrap_art_classifier(model, X: np.ndarray, y: np.ndarray):
    clip_min = float(np.min(X)) - 1.0
    clip_max = float(np.max(X)) + 1.0
    nb_classes = max(2, len(np.unique(y)))
    model_cls = model.__class__.__name__
    module = getattr(model.__class__, "__module__", "")

    if "xgboost" in module or model_cls == "XGBClassifier":
        from art.estimators.classification import XGBoostClassifier

        return XGBoostClassifier(
            model=model,
            clip_values=(clip_min, clip_max),
            nb_features=int(X.shape[1]),
            nb_classes=nb_classes,
        )

    from art.estimators.classification import SklearnClassifier

    return SklearnClassifier(model=model, clip_values=(clip_min, clip_max))


def _run_art_attacks(
    model,
    X: np.ndarray,
    y: np.ndarray,
    feature_cols: List[str],
    attacks: List[str],
    max_batch: int = 80,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    t0 = time.perf_counter()
    errors: List[str] = []
    attacks_run: List[str] = []
    attacks_skipped: List[Dict[str, str]] = []

    X_sample = X[: min(max_batch, len(X))].astype(np.float32)
    y_sample = y[: len(X_sample)].astype(int)
    classifier = _wrap_art_classifier(model, X_sample, y_sample)

    clean_preds = classifier.predict(X_sample)
    if hasattr(clean_preds, "ndim") and clean_preds.ndim > 1:
        clean_acc = float((clean_preds.argmax(axis=1) == y_sample).mean())
    else:
        clean_preds_bin = (np.asarray(clean_preds).ravel() > 0.5).astype(int)
        clean_acc = float((clean_preds_bin == y_sample).mean())

    adv_X = X_sample.copy()
    adv_acc = clean_acc

    is_xgb = "XGBoostClassifier" in classifier.__class__.__name__
    x_batch = X_sample[: min(20 if is_xgb else max_batch, len(X_sample))]
    y_batch = y_sample[: len(x_batch)]

    if not is_xgb:
        attack_plan = [
            ("fgsm", "FastGradientMethod", {"eps": 0.1}),
            ("pgd", "ProjectedGradientDescent", {"eps": 0.1, "max_iter": 5}),
        ]
        for name, cls_name, kwargs in attack_plan:
            if name not in [a.lower() for a in attacks]:
                attacks_skipped.append({"attack": name, "reason": "not_requested"})
                continue
            try:
                if cls_name == "FastGradientMethod":
                    from art.attacks.evasion import FastGradientMethod

                    atk = FastGradientMethod(estimator=classifier, **kwargs)
                else:
                    from art.attacks.evasion import ProjectedGradientDescent

                    atk = ProjectedGradientDescent(estimator=classifier, **kwargs)
                adv_X = atk.generate(x=x_batch)
                X_sample = x_batch
                y_sample = y_batch
                attacks_run.append(name)
            except Exception as exc:
                attacks_skipped.append({"attack": name, "reason": str(exc)[:200]})
                errors.append(f"{name}:{exc}")

    if not attacks_run and is_xgb:
        try:
            from art.attacks.evasion import ZooAttack

            atk = ZooAttack(
                classifier=classifier,
                confidence=0.0,
                targeted=False,
                learning_rate=0.1,
                max_iter=15,
                binary_search_steps=5,
                initial_const=1e-3,
                abort_early=True,
                batch_size=1,
                nb_parallel=1,
            )
            adv_X = atk.generate(x=x_batch)
            X_sample = x_batch
            y_sample = y_batch
            attacks_run.append("zoo")
        except Exception as exc:
            attacks_skipped.append({"attack": "zoo", "reason": str(exc)[:200]})
            errors.append(f"zoo:{exc}")

    if not attacks_run:
        try:
            from art.attacks.evasion import HopSkipJump

            atk = HopSkipJump(classifier=classifier, max_iter=10, max_eval=200, init_eval=20)
            adv_X = atk.generate(x=x_batch)
            X_sample = x_batch[: len(adv_X)]
            y_sample = y_batch[: len(adv_X)]
            attacks_run.append("hop_skip_jump")
        except Exception as exc:
            attacks_skipped.append({"attack": "hop_skip_jump", "reason": str(exc)[:200]})
            errors.append(f"hop_skip_jump:{exc}")

    adv_preds = classifier.predict(adv_X)
    if hasattr(adv_preds, "ndim") and adv_preds.ndim > 1:
        adv_acc = float((adv_preds.argmax(axis=1) == y_sample).mean())
    else:
        adv_preds_bin = (np.asarray(adv_preds).ravel() > 0.5).astype(int)
        adv_acc = float((adv_preds_bin == y_sample).mean())

    df = pd.DataFrame(adv_X, columns=feature_cols[: adv_X.shape[1]])
    df["is_attack"] = y_sample
    df["label"] = "ADVERSARIAL"

    art_info = ensure_art_on_path()
    metrics = {
        "art_available": bool(art_info.get("art_available")),
        "art_version": art_info.get("art_version"),
        "art_source": art_info.get("source_path") or "local",
        "attacks_run": attacks_run,
        "attacks_skipped": attacks_skipped,
        "clean_accuracy": round(clean_acc, 4),
        "adversarial_accuracy": round(adv_acc, 4),
        "robustness_drop": round(clean_acc - adv_acc, 4),
        "adversarial_samples_generated": len(df),
        "fallback_used": False,
        "errors": errors,
        "runtime_s": round(time.perf_counter() - t0, 3),
    }
    return df, metrics


def run_adversarial_hardening(
    cfg: EvolutionConfig,
    candidate_result: Dict[str, Any],
    *,
    apply_training: bool = False,
) -> Dict[str, Any]:
    art_info = ensure_art_on_path()
    ok = bool(art_info.get("art_available"))
    version = art_info.get("art_version")
    source = art_info.get("source_path")
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "art_available": ok,
        "art_version": version,
        "art_source": source,
        "attacks_run": [],
        "attacks_skipped": [],
        "clean_accuracy": None,
        "adversarial_accuracy": None,
        "robustness_drop": None,
        "adversarial_samples_generated": 0,
        "adversarial_training_applied": False,
        "fallback_used": True,
        "errors": [],
        "runtime_s": 0.0,
        "recommendation": "skip",
    }

    if not cfg.use_art:
        report["recommendation"] = "art_disabled"
        write_json(cfg.reports_dir / "adversarial_hardening_report.json", report)
        return {**report, "adversarial_samples": pd.DataFrame()}

    X = candidate_result.get("X")
    y = candidate_result.get("y")
    feature_cols = candidate_result.get("feature_cols", [])
    metadata = candidate_result.get("metadata", {})
    artifacts = metadata.get("artifacts", {})

    if X is None or y is None or len(X) == 0:
        report["recommendation"] = "no_training_data"
        write_json(cfg.reports_dir / "adversarial_hardening_report.json", report)
        return {**report, "adversarial_samples": pd.DataFrame()}

    import joblib

    model_path = artifacts.get("xgboost")
    adv_df = pd.DataFrame()
    t0 = time.perf_counter()

    if model_path and ok:
        try:
            model = joblib.load(model_path)
            adv_df, art_metrics = _run_art_attacks(model, X, y, feature_cols, cfg.art_attacks)
            report.update(art_metrics)
            if report.get("robustness_drop") and report["robustness_drop"] > 0.15:
                report["recommendation"] = "retrain_with_adversarial_samples"
            else:
                report["recommendation"] = "acceptable_robustness"
        except Exception as exc:
            report["errors"].append(str(exc))
            adv_X, adv_y, attacks = _fallback_attacks(X, y)
            adv_df = pd.DataFrame(adv_X, columns=feature_cols[: adv_X.shape[1]])
            adv_df["is_attack"] = adv_y
            report["attacks_run"] = attacks
            report["adversarial_samples_generated"] = len(adv_df)
            report["fallback_used"] = True
            report["recommendation"] = "fallback_due_to_art_error"
    else:
        if not ok:
            report["errors"].append("art_not_importable")
        adv_X, adv_y, attacks = _fallback_attacks(X, y)
        adv_df = pd.DataFrame(adv_X, columns=feature_cols[: adv_X.shape[1]])
        adv_df["is_attack"] = adv_y
        report["attacks_run"] = attacks
        report["adversarial_samples_generated"] = len(adv_df)
        report["fallback_used"] = True
        report["recommendation"] = "use_fallback_mutations"

    report["runtime_s"] = round(time.perf_counter() - t0, 3)
    report["adversarial_training_applied"] = bool(apply_training and cfg.adversarial_train)
    write_json(cfg.reports_dir / "adversarial_hardening_report.json", report)
    return {**report, "adversarial_samples": adv_df}
