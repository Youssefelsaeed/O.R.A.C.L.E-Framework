# ORACLE Final Metrics Truth

ORACLE must not be presented with one global perfect accuracy. Metrics are valid only for the dataset, schema path, detector, sample balance, and runtime path that produced them.

## Old MutantShield Mixed Validation

| Source | Accuracy | Precision | Recall | F1 | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Mixed CIC/UNSW historical validation | 0.7425 | 0.8173 | 0.6114 | 0.6995 | Historical train/validation-style evidence; not a full-stack runtime proof and not equivalent to controlled external per-dataset validation. |

## New Controlled Standalone Results

| Path | Accuracy | Precision | Recall | F1 | Use In Presentation? | Reason |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| CIC production FusionEngine | 0.95 | 1.0 | 0.9 | 0.9474 | True | direct controlled path |
| UNSW mapped path | 0.47 | 0.0 | 0.0 | 0.0 | False | mapped_schema_warning |
| CSE production FusionEngine | 0.5 | 0.0 | 0.0 | 0.0 | True | direct controlled path |
| CSE repair candidate | 0.975 | 0.9524 | 1.0 | 0.9756 | True | candidate_only |
| DoHBrw mapped path | 0.5 | 0.0 | 0.0 | 0.0 | False | mapped_schema_warning, adapter_required |
| DoHBrw native adapter | 0.89 | 0.8197 | 1.0 | 0.9009 | True | adapter_required |

## Why Some Results Are 0.0

- CSE production baseline and DoHBrw mapped baseline produce 0.0 recall because the production/mapped path did not emit attack predictions on the controlled positive rows.
- UNSW is a mapped schema validation path; it is not a native production claim.
- DoHBrw requires the native adapter for meaningful anomaly detection.
- CSE improved only through the candidate repair path, which remains candidate-only and must not be described as promoted production.

## Full Stack Runtime

- Full-stack runtime proof pass: `True`
- Full-stack metrics are in `docs/FULL_STACK_DETECTION_PROOF.md` and are valid only when `/oracle/runtime-info` proves `phase12_19_current_runtime`.

## Recommended Presentation Format

- Show old mixed CIC/UNSW validation as historical baseline only.
- Show CIC production FusionEngine as the direct production controlled path.
- Show CSE production baseline and CSE repair candidate separately.
- Show DoHBrw mapped baseline and DoHBrw native adapter separately.
- Show full ORACLE stack reliability/audit metrics separately from detector quality.
