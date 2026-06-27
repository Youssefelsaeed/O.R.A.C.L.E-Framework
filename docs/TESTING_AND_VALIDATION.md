# Testing And Validation

O.R.A.C.L.E Framework has been validated through backend, production-like simulation, module capability, API contract, concurrency, soak, and acceptance testing.

## Framework Status

- `ORACLE_MODULE_CAPABILITY_VALIDATED`
- `ORACLE_FULLY_TESTED_AND_READY`
- `ORACLE_FINAL_QA_COMPLETE`

## Backend Benchmark

- 300 success
- 0 degraded
- 0 failed
- p95 latency 197.56 ms

## Production-Like Simulation

- 1000 events
- 0 degraded
- 0 failed
- Historical CSE/DoHBrw recall values are not treated as banner truth unless reconfirmed by Phase 12.18 per-dataset evaluation.

## Phase 12.18B Controlled Detection Verification

Fresh detection metrics must come from:

- `reports/final/phase12_18b_eval_set_summary.json`
- `reports/final/phase12_18b_detector_routing_audit.json`
- `reports/final/phase12_18b_mutantshield_controlled_eval.json`
- `reports/final/phase12_18b_full_stack_controlled_eval.json`
- `reports/final/ORACLE_FINAL_DETECTION_VERDICT.json`

If runtime proof fails, full-stack metrics are blocked instead of being reported from a stale Oracle Core process.

Latest Phase 12.18B controlled standalone MutantShield results:

| Dataset / Path | Rows | Accuracy | Precision | Recall | F1 | FPR | FNR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CIC-IDS2017 production FusionEngine | 124 | 0.9274 | 1.0 | 0.625 | 0.7692 | 0.0 | 0.375 |
| UNSW-NB15 mapped validation | 200 | 0.48 | 0.1667 | 0.01 | 0.0189 | 0.05 | 0.99 |
| CSE-CIC-IDS2018 production FusionEngine | 200 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 |
| CSE-CIC-IDS2018 HOIC repair candidate | 200 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 |
| DoHBrw mapped CIC | 200 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 |
| DoHBrw native adapter | 200 | 0.89 | 0.8197 | 1.0 | 0.9009 | 0.22 | 0.0 |

Full-stack controlled evaluation is currently `BLOCKED_RUNTIME_NOT_CURRENT`: `/oracle/runtime-info` returned 404 from the running core, so Oracle preservation metrics were not claimed.

## Module Validation Highlights

- MutantShield: Excellent
- QAuthCore: Excellent, 1000 unique tokens, uniqueness 1.0, verification 1.0, assurance pending/failed 0/0
- EthicQ: Excellent, rationality matrix 12/12
- ChronoLedger: Excellent with legacy chain warning, append success 1.0, invalid rejection 1.0, concurrent success 1.0
- GhostTunnel: Excellent, accepted 24, failed 0, p95 ack latency 65.86 ms
- Evolution Engine: Good, candidate-only retraining and promotion gates
- Oracle GUI: Good

## Notes

Generated reports are kept local and are not part of the production GitHub upload. Detailed historical validation remains under local `reports/` and in `docs/ORACLE_TESTING_REPORT.md`.
