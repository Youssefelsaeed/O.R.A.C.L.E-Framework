# LSTM Candidate-Safe Retraining Contract

## Purpose

This contract defines when MutantShield Evolution Engine may retrain an LSTM candidate. Production LSTM inference remains active, but candidate retraining is allowed only when the temporal input schema, metadata, output paths, and safety gates below are satisfied.

## Required Input Schema

The LSTM training buffer must be a tabular dataset with one row per flow timestep. Required columns:

- `sequence_id`: stable identifier grouping rows into one temporal sequence.
- `sequence_index`: zero-based or one-based timestep order within `sequence_id`.
- `timestamp`: parseable event time or monotonic flow time.
- `flow_id`: unique flow identifier.
- `label`: class label used for training.
- `is_attack`: binary attack target, `0` or `1`.
- `attack_family`: attack family or `benign`.
- Production feature columns in the exact MutantShield feature order from `feature_schema.json`.

## Required Temporal Sequence Format

- Rows must be sorted by `sequence_id`, then `sequence_index` or `timestamp`.
- Each sequence must contain at least 15 timesteps by default.
- Sequence windows must preserve real chronological order. Static row duplication, random shuffling inside a sequence, or averaged-window surrogates are forbidden.
- Labels must be derived from trusted dataset labels or verified adaptation buffers.

## Required Feature Order

Training must use the production 78-feature MutantShield order when available. The candidate metadata must persist:

- `feature_order`
- `sequence_length`
- `label_mapping`
- `scaler_type`
- `training_source`
- `contract_version`

## Required Metadata Fields

`lstm_candidate_metadata.json` must include:

- `candidate_id`
- `model_family`: `LSTM`
- `contract_name`: `lstm_retraining_contract`
- `contract_version`
- `created_at`
- `feature_order`
- `sequence_length`
- `label_mapping`
- `scaler_type`
- `training_rows`
- `training_sequences`
- `validation_sequences`
- `source_datasets`
- `models_final_unchanged`: `true`
- `promotion_eligible`: `false` unless all ensemble gates pass

## Required Output Artifacts

All LSTM candidate outputs must be written only under:

`models_candidate/<candidate_id>/LSTM_Optimized/`

Required artifacts:

- `lstm_candidate_model.*`
- `lstm_candidate_weights.*`
- `lstm_candidate_metadata.json`
- `lstm_training_report.json`

## Forbidden Output Directories

The LSTM retrainer must never write to:

- `models_final/`
- `Mutant_Sheild Module/mutantshield/src/FinalVersion/models_final/`
- `models_archive/` unless explicitly archiving a candidate after validation
- Any production FusionEngine, XGBoost, AutoEncoder, GNN, or GAN directory

## Validation Gates Before Training

Training is blocked unless:

- Required columns are present.
- Production feature order is available and matched.
- Sequence grouping and timestep ordering are valid.
- Minimum sequence length is satisfied.
- Labels are trusted and binary target is present.
- Candidate output path resolves under `models_candidate/<candidate_id>/LSTM_Optimized/`.
- `models_final` hash snapshot is recorded before training.

## Rollback and Safety Requirements

- Candidate training must be dry-run/candidate-only by default.
- Promotion remains blocked until full ensemble retraining, adversarial evaluation, benchmark comparison, human approval, and `models_final` hash audit all pass.
- Failed training must write `lstm_training_report.json` with `status=blocked` or `status=failed`.
- Surrogate models must not be labeled as real LSTM retraining.
