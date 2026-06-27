# ORACLE Final Detection Verdict

Final Status: `NOT_READY`

- Did we generate flows from datasets? `True`
- Did we test MutantShield alone? `True`
- Did we test full ORACLE stack? `False`
- Does Oracle Core use real MutantShield output? `False`

## Presentation Metrics
Use only Phase 12.18B per-dataset/path metrics with final_claim_valid=true; do not use unsupported banner metrics.

## Remaining Limits
- Paths with weak recall/F1 in controlled evaluation.
- UNSW as native production claim because it is mapped validation.
- CSE repair candidate when no candidate bundle is present.
