# ORACLE MutantShield Final Detection Results

Metrics are mean +/- population std across seeds 42, 1337, and 2026. These are controlled dataset evaluations, not guaranteed real-network deployment performance.

| Path | Accuracy | Precision | Recall | F1 | FPR | FNR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CIC production FusionEngine | 0.76 +/- 0.0196 | 1.0 +/- 0.0 | 0.52 +/- 0.0392 | 0.6833 +/- 0.0336 | 0.0 +/- 0.0 | 0.48 +/- 0.0392 |
| UNSW mapped production path | 0.4622 +/- 0.0063 | 0.1217 +/- 0.0919 | 0.0133 +/- 0.0109 | 0.024 +/- 0.0194 | 0.0889 +/- 0.0063 | 0.9867 +/- 0.0109 |
| CSE production FusionEngine | 0.46 +/- 0.0189 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | 0.08 +/- 0.0377 | 1.0 +/- 0.0 |
| CSE repair candidate | 0.9689 +/- 0.0083 | 0.9733 +/- 0.0107 | 0.9645 +/- 0.0166 | 0.9687 +/- 0.0084 | 0.0267 +/- 0.0109 | 0.0355 +/- 0.0166 |
| DoHBrw mapped production path | 0.5 +/- 0.0 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | 0.0 +/- 0.0 | 1.0 +/- 0.0 |
| DoHBrw native adapter | 0.9 +/- 0.0283 | 0.8375 +/- 0.0392 | 0.9956 +/- 0.0063 | 0.9093 +/- 0.0241 | 0.1956 +/- 0.0537 | 0.0044 +/- 0.0063 |
