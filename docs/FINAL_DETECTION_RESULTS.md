# Final Detection Results

These are Phase 12.19 controlled standalone MutantShield results. Full-stack proof is documented separately.

| Path | Rows | Benign | Attack | Accuracy | Precision | Recall | F1 | FPR | FNR | Valid Final Claim | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| CIC production FusionEngine | 200 | 100 | 100 | 0.95 | 1.0 | 0.9 | 0.9474 | 0.0 | 0.1 | True | none |
| UNSW mapped path | 200 | 100 | 100 | 0.47 | 0.0 | 0.0 | 0.0 | 0.06 | 1.0 | False | mapped_schema_warning |
| CSE production FusionEngine | 200 | 100 | 100 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | True | none |
| CSE repair candidate | 200 | 100 | 100 | 0.975 | 0.9524 | 1.0 | 0.9756 | 0.05 | 0.0 | True | candidate_only |
| DoHBrw mapped path | 200 | 100 | 100 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | False | adapter_required, mapped_schema_warning |
| DoHBrw native adapter | 200 | 100 | 100 | 0.89 | 0.8197 | 1.0 | 0.9009 | 0.22 | 0.0 | True | adapter_required |

Do not present these as one global accuracy. Use the per-path values and limitations.
