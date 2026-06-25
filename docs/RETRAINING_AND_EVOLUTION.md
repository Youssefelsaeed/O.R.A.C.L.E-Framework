# Retraining And Evolution

The Evolution Engine is designed to adapt detection capability without compromising production model safety.

## Candidate-Only Workflow

- Candidate artifacts are created outside `models_final`.
- Candidates are evaluated before routing or promotion.
- Promotion is blocked unless safety gates pass.
- Human approval, adversarial evaluation, rollback planning, and model hash auditing are required for production promotion.

## Supported And Gated Paths

- XGBoost candidate retraining: supported.
- AutoEncoder candidate retraining: supported.
- LSTM retraining: contract-gated; inference remains active.
- GNN retraining: contract-gated; inference remains active.
- GAN synthetic generation: roadmap/future work.

## Evidence Policy

ChronoLedger evidence supports auditability and traceability. It is not automatically trusted as training data. Supervised training requires reviewed evidence and explicit approval.

Detailed evolution documentation remains in `docs/ORACLE_RETRAINING_LOOP.md`.
