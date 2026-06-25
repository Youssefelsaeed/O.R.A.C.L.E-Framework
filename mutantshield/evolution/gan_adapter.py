"""Optional GAN adapter — load trained artifacts only; never emit placeholder GAN samples."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from .config import EvolutionConfig
from .reports import write_json


def _has_trained_generator(cfg: EvolutionConfig) -> bool:
    gan_dir = cfg.gan_artifacts_dir
    if not gan_dir.exists():
        return False
    generator_markers = (
        list(gan_dir.glob("generator*.pt"))
        + list(gan_dir.glob("generator*.pth"))
        + list(gan_dir.glob("gan_generator.pkl"))
    )
    scaler_markers = list(gan_dir.glob("scaler.pkl")) + list(gan_dir.glob("gan_scaler.pkl"))
    meta_path = gan_dir / "gan_metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") == "trained" and meta.get("generator_path"):
            return Path(meta["generator_path"]).exists()
    return bool(generator_markers and scaler_markers)


def gan_available(cfg: EvolutionConfig) -> bool:
    return _has_trained_generator(cfg)


def load_gan_metadata(cfg: EvolutionConfig) -> Dict[str, Any]:
    meta_path = cfg.gan_artifacts_dir / "gan_metadata.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    if _has_trained_generator(cfg):
        return {"status": "trained", "artifacts_dir": str(cfg.gan_artifacts_dir)}
    return {
        "status": "not_trained",
        "artifacts_dir": str(cfg.gan_artifacts_dir),
        "recommendation": "train_gan_later",
    }


def generate_synthetic_attacks(cfg: EvolutionConfig, n_samples: int = 1000) -> pd.DataFrame:
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "n_requested": n_samples,
        "status": "not_trained",
        "samples_generated": 0,
        "gan_training_required": True,
        "recommendation": "train_gan_later",
    }

    if not cfg.use_gan:
        report["status"] = "skipped_disabled"
        write_json(cfg.reports_dir / "gan_generation_report.json", report)
        return pd.DataFrame()

    if not _has_trained_generator(cfg):
        report["status"] = "not_trained"
        write_json(cfg.reports_dir / "gan_generation_report.json", report)
        return pd.DataFrame()

    try:
        samples_path = cfg.gan_artifacts_dir / "generated_samples.npy"
        if samples_path.exists():
            arr = np.load(samples_path)
            take = min(n_samples, len(arr))
            df = pd.DataFrame(arr[:take])
            df.columns = [f"feature_{i}" for i in range(df.shape[1])]
            report["status"] = "available"
            report["samples_generated"] = take
            report["gan_training_required"] = False
            report["source"] = "precomputed_npy"
            write_json(cfg.reports_dir / "gan_generation_report.json", report)
            return df
        report["status"] = "not_trained"
        report["note"] = "Generator artifacts exist but no precomputed samples; train GAN before use"
        write_json(cfg.reports_dir / "gan_generation_report.json", report)
        return pd.DataFrame()
    except Exception as exc:
        report["status"] = "error"
        report["error"] = str(exc)
        write_json(cfg.reports_dir / "gan_generation_report.json", report)
        return pd.DataFrame()
