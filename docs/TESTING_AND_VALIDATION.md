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
- Historical CSE/DoHBrw recall values are not treated as banner truth unless reconfirmed by Phase 12.19 per-path evaluation.

## Phase 12.19 Controlled Detection Verification

Fresh detection metrics must come from:

- `docs/FINAL_DETECTION_RESULTS.md`
- `docs/FULL_STACK_DETECTION_PROOF.md`
- `docs/ORACLE_FINAL_METRICS_TRUTH.md`

If runtime proof fails, full-stack metrics are blocked instead of being reported from a stale Oracle Core process.

Latest Phase 12.19 controlled standalone MutantShield results:

| Dataset / Path | Rows | Accuracy | Precision | Recall | F1 | FPR | FNR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CIC-IDS2017 production FusionEngine | 200 | 0.95 | 1.0 | 0.9 | 0.9474 | 0.0 | 0.1 |
| UNSW-NB15 mapped validation | 200 | 0.47 | 0.0 | 0.0 | 0.0 | 0.06 | 1.0 |
| CSE-CIC-IDS2018 production FusionEngine | 200 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 |
| CSE-CIC-IDS2018 HOIC repair candidate | 200 | 0.975 | 0.9524 | 1.0 | 0.9756 | 0.05 | 0.0 |
| DoHBrw mapped CIC | 200 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 |
| DoHBrw native adapter | 200 | 0.89 | 0.8197 | 1.0 | 0.9009 | 0.22 | 0.0 |

Full-stack controlled evaluation passed after `/oracle/runtime-info` proved `phase12_19_current_runtime`: all tested rows were accepted, detector fields were preserved, and audit/auth rates were `1.0`.

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
