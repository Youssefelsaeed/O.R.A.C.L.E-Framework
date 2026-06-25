"""Evolution Engine configuration — safe defaults, dry-run by default."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
FINAL_VERSION = ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion"


class EvolutionConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVOLUTION_", extra="ignore")

    enabled: bool = Field(default=True, validation_alias="EVOLUTION_ENABLED")
    dry_run: bool = Field(default=True, validation_alias="EVOLUTION_DRY_RUN")
    auto_promote: bool = Field(default=False, validation_alias="EVOLUTION_AUTO_PROMOTE")
    min_samples: int = Field(default=100, validation_alias="EVOLUTION_MIN_SAMPLES")
    max_samples: int = Field(default=5000, validation_alias="EVOLUTION_MAX_SAMPLES")
    use_chronoledger: bool = Field(default=True, validation_alias="EVOLUTION_USE_CHRONOLEDGER")
    use_datasets: bool = Field(default=True, validation_alias="EVOLUTION_USE_DATASETS")
    use_gan: bool = Field(default=False, validation_alias="EVOLUTION_USE_GAN")
    use_art: bool = Field(default=True, validation_alias="EVOLUTION_USE_ART")
    art_attacks: List[str] = Field(default_factory=lambda: ["fgsm", "pgd"])
    target_models: List[str] = Field(
        default_factory=lambda: ["xgboost", "autoencoder", "lstm", "gnn", "fusion", "gan"]
    )
    require_human_approval_for_chrono: bool = Field(
        default=True, validation_alias="EVOLUTION_REQUIRE_HUMAN_APPROVAL_FOR_CHRONO"
    )
    force_promote: bool = Field(default=False, validation_alias="EVOLUTION_FORCE_PROMOTE")
    mode: str = Field(default="candidate-only", validation_alias="EVOLUTION_MODE")
    adversarial_train: bool = Field(default=True, validation_alias="EVOLUTION_ADVERSARIAL_TRAIN")
    skip_adversarial: bool = Field(default=False, validation_alias="EVOLUTION_SKIP_ADVERSARIAL")
    human_approval_token: str = Field(default="", validation_alias="EVOLUTION_HUMAN_APPROVAL_TOKEN")
    full_ensemble: bool = Field(default=True, validation_alias="EVOLUTION_FULL_ENSEMBLE")
    include_cse_buffer: str = Field(default="", validation_alias="EVOLUTION_INCLUDE_CSE_BUFFER")
    synthetic_mode: str = Field(default="disabled", validation_alias="EVOLUTION_SYNTHETIC_MODE")

    @property
    def root(self) -> Path:
        return ROOT

    @property
    def reports_dir(self) -> Path:
        return ROOT / "reports" / "evolution"

    @property
    def models_candidate_dir(self) -> Path:
        return ROOT / "models_candidate"

    @property
    def models_archive_dir(self) -> Path:
        return ROOT / "models_archive"

    @property
    def models_final_dir(self) -> Path:
        return FINAL_VERSION / "models_final"

    @property
    def models_registry_dir(self) -> Path:
        return ROOT / "models_registry"

    @property
    def dataset_registry_path(self) -> Path:
        return self.models_registry_dir / "dataset_registry.json"

    @property
    def model_versions_path(self) -> Path:
        return self.models_registry_dir / "model_versions.json"

    @property
    def gan_artifacts_dir(self) -> Path:
        return self.models_final_dir / "GAN"

    @property
    def default_cic_path(self) -> Path:
        return FINAL_VERSION / "Data set" / "CIC-2017 (baseline)"

    @property
    def default_unsw_path(self) -> Path:
        return FINAL_VERSION / "Data set" / "UNWB-2015" / "UNSW_NB15_training-set.csv"


def get_config(**overrides: object) -> EvolutionConfig:
    cfg = EvolutionConfig()
    for k, v in overrides.items():
        if hasattr(cfg, k):
            object.__setattr__(cfg, k, v)
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    cfg.models_candidate_dir.mkdir(parents=True, exist_ok=True)
    cfg.models_archive_dir.mkdir(parents=True, exist_ok=True)
    cfg.models_registry_dir.mkdir(parents=True, exist_ok=True)
    return cfg
