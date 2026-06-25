# GNN Candidate-Safe Retraining Contract

## Purpose

This contract defines when MutantShield Evolution Engine may retrain a GNN candidate. Production GNN inference remains active, but candidate retraining is allowed only when graph construction data and safety gates are available.

## Required Graph Input Schema

The GNN training buffer must preserve flow graph context. Required columns:

- `flow_id`: unique flow identifier.
- `src_ip`: source host identity.
- `dst_ip`: destination host identity.
- `timestamp`: parseable event time used for temporal graph windows.
- `label`: class label.
- `is_attack`: binary target, `0` or `1`.
- `attack_family`: attack family or `benign`.
- Edge feature columns in the MutantShield feature order.

Optional but recommended columns:

- `protocol`
- `src_port`
- `dst_port`
- `source_dataset`
- `source_file`
- `label_trust`

## Node Identity Mapping

- Node IDs must be derived from normalized `src_ip` and `dst_ip` values.
- The candidate builder must persist a deterministic `node_mapping`.
- Inference-time unknown nodes must use a documented fallback strategy without mutating production builder files.

## Graph Construction Rules

- Nodes are hosts.
- Edges are flows from `src_ip` to `dst_ip`.
- Edge attributes are numeric flow features in the documented feature order.
- Graphs must be built in chronological windows from `timestamp`.
- Training must not reconstruct graphs from buffers that lack source/destination/time metadata.
- Graph labels must be derived from trusted row labels or documented aggregation rules.

## Graph Split Rules

- Train/validation/test splits must avoid temporal leakage.
- Graph windows should be split chronologically where possible.
- Rows from the same `flow_id` must not appear in multiple splits.
- Node mapping and scaler must be fit on training split only and persisted for candidate inference.

## Candidate Artifact Outputs

All GNN candidate outputs must be written only under:

`models_candidate/<candidate_id>/GNN/`

Required artifacts:

- `gnn_candidate.pth`
- `gnn_candidate_builder.pkl`
- `gnn_candidate_metadata.json`
- `gnn_training_report.json`

## Forbidden Writes

The GNN retrainer must never write to:

- `models_final/`
- `Mutant_Sheild Module/mutantshield/src/FinalVersion/models_final/`
- `Mutant_Sheild Module/mutantshield/src/FinalVersion/models_final/GNN/`
- Any production FusionEngine, LSTM, XGBoost, AutoEncoder, or GAN directory

## Validation Gates Before Training

Training is blocked unless:

- Required graph columns are present.
- `src_ip`, `dst_ip`, and `timestamp` are non-empty for training rows.
- Numeric edge features are available.
- Node mapping can be built deterministically.
- Temporal graph windows can be constructed.
- Candidate output path resolves under `models_candidate/<candidate_id>/GNN/`.
- `models_final` hash snapshot is recorded before training.

## Rollback and Safety Requirements

- Candidate training must be dry-run/candidate-only by default.
- Failed graph construction must write `gnn_training_report.json` with `status=blocked` or `status=failed`.
- Promotion remains blocked until all ensemble retraining contracts, adversarial evaluation, benchmark comparison, human approval, and `models_final` hash audit pass.
- Synthetic or inferred graph structure must not be treated as proof of real GNN retraining.
