# Module Capabilities

Validated framework status:

- `ORACLE_MODULE_CAPABILITY_VALIDATED`
- `ORACLE_FULLY_TESTED_AND_READY`
- `ORACLE_FINAL_QA_COMPLETE`

## Capability Scores

| Module | Capability | Score | Notes |
| --- | --- | --- | --- |
| Oracle Core | Orchestration and API coordination | Excellent | Central event pipeline and dashboard APIs validated. |
| MutantShield | AI detection and adapter-based analysis | Evidence-gated | Use Phase 12.18B controlled reports for CIC, UNSW mapped validation, CSE production/candidate, DoHBrw mapped, and DoHBrw native metrics. Historical high recall values are not banner truth unless freshly reconfirmed. |
| QAuthCore | Token assurance and async assurance | Excellent | 1000 unique tokens; uniqueness 1.0; verification 1.0. |
| EthicQ | Ethical response governance | Excellent | Rationality matrix 12/12. |
| ChronoLedger | Tamper-evident audit logging | Excellent | Append success 1.0; invalid rejection 1.0; concurrent success 1.0; legacy chain warning documented. |
| GhostTunnel | Secure response/transmission queue | Excellent | Accepted 24; failed 0; p95 ack latency 65.86 ms. |
| Evolution Engine | Candidate-only retraining and hardening | Good | XGBoost/AutoEncoder supported; LSTM/GNN retraining contract-gated. |
| Oracle GUI | Operator dashboard | Good | Runtime health and framework state visible. |

## Professional Limitations

- Unknown domains require adapters or reviewed evidence.
- Detection metrics must be reported per dataset and per path: Production FusionEngine, CSE repair candidate, DoHBrw mapped path, DoHBrw native adapter, and full ORACLE stack.
- Phase 12.18B controlled standalone results: CIC production recall `0.625`, UNSW mapped recall `0.01`, CSE production recall `0.0`, CSE HOIC repair candidate recall `1.0`, DoHBrw mapped recall `0.0`, DoHBrw native-adapter recall `1.0`.
- Full ORACLE stack detection metrics are currently blocked because `/oracle/runtime-info` did not prove the `phase12_18b_runtime` marker on the running core.
- LSTM/GNN retraining is contract-gated; inference remains active.
- GAN synthetic generation is roadmap/future work.
- Production deployment requires environment-specific hardening.
