# ORACLE Final Capability Matrix

## What ORACLE Can Detect

- CIC/CICFlowMeter-style traffic families supported by MutantShield production ensemble
- CSE attacks validated by repair candidate: Web, XSS, SQL Injection, LOIC, HOIC
- DoHBrw-native anomaly traffic through DoHBrwAdapter
- malformed payloads and invalid requests at Oracle Core validation level

## Detection Metrics Source Of Truth

Phase 12.18 replaces banner-style global detection claims with per-dataset evidence:

- `phase12_18_feature_mapping_audit.json`
- `phase12_18_mutantshield_standalone_eval.json`
- `phase12_18_full_stack_dataset_eval.json`
- `phase12_18_metric_truth_comparison.json`

If a raw dataset is absent, the corresponding result is `BLOCKED_MISSING_DATASET`; no substitute metric is inferred from historical reports.

Latest bounded Phase 12.18 evidence:

| Dataset / Path | Feature Mapping | Rows | Recall | F1 | Note |
| --- | ---: | ---: | ---: | ---: | --- |
| CIC-IDS2017 mapped CIC | 1.0 | 50 | 0.0 | 0.0 | Sample was benign-only; do not infer attack recall. |
| UNSW-NB15 mapped CIC | 0.5 | 50 | 0.0 | 0.0 | Partial semantic mapping; domain-transfer only. |
| CSE-CIC-IDS2018 mapped CIC | 0.9872 | 50 | 0.0 | 0.0 | Fresh audit did not confirm historical CSE recall. |
| DoHBrw mapped CIC | 0.0 | 50 | 0.0 | 0.0 | CIC path is incompatible. |
| DoHBrw native adapter | native | 50 | 0.0 | 0.0 | Fresh bounded sample did not confirm historical adapter recall. |

## What ORACLE Can Learn

- new attack distributions through candidate-only XGBoost/AutoEncoder retraining
- CSE repair patterns
- DoHBrw domain-specific anomaly adapters
- adversarially hardened candidate behavior
- future LSTM/GNN retraining when contracts are satisfied
- future GAN synthetic attacks when trained and quality-gated

## Current Limitations

- cannot safely retrain LSTM/GNN until temporal/graph contracts pass
- GAN synthetic generation deferred
- SIEM/SOAR/EDR external integration pending
- production promotion blocked by design
- datasets not included in GitHub
- detection outside validated domains requires new adapters or reviewed evidence
- one global accuracy/recall number is not used; metrics must be separated by dataset and detection path
