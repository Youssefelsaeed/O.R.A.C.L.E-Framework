# ORACLE Presentation Metrics Final

These metrics are from dataset replay and controlled evaluation, not guaranteed real-network deployment performance.

| Metric Area | Accuracy | Precision | Recall | F1 | Presentation Note |
| --- | ---: | ---: | ---: | ---: | --- |
| CIC production FusionEngine | 0.76 +/- 0.0196 | 1.0 +/- 0.0 | 0.52 +/- 0.0392 | 0.6833 +/- 0.0336 | Primary in-domain production path. |
| Mixed CIC/UNSW historical baseline | 0.7425 | 0.8173 | 0.6114 | 0.6995 | Historical baseline only. |
| UNSW mapped path | 0.4622 +/- 0.0063 | 0.1217 +/- 0.0919 | 0.0133 +/- 0.0109 | 0.024 +/- 0.0194 | Weak generalization; not final production claim. |
| CSE production baseline | 0.46 +/- 0.0189 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | Honest baseline. |
| CSE repair candidate | 0.9689 +/- 0.0083 | 0.9733 +/- 0.0107 | 0.9645 +/- 0.0166 | 0.9687 +/- 0.0084 | Candidate-only; not promoted production. |
| DoHBrw mapped path | 0.5 +/- 0.0 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | Adapter required. |
| DoHBrw native adapter | 0.9 +/- 0.0283 | 0.8375 +/- 0.0392 | 0.9956 +/- 0.0063 | 0.9093 +/- 0.0241 | Native adapter path. |

## Full ORACLE Stack Reliability

- Field preservation: `1.0`
- Audit rate: `1.0`
- Auth rate: `1.0`
- Degraded/failed: `0` / `0`
- Average p95 latency across repeated paths: `186.2068` ms
