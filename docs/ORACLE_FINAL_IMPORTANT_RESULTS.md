# ORACLE Final Important Results

This document contains the concise, presentation-safe results for Project O.R.A.C.L.E. It avoids raw report dumps and does not replace production validation in a real deployment environment.

## Runtime And Stack Readiness

- Oracle Core current runtime proof passed with `/oracle/runtime-info`.
- Full stack processing passed after the stale runtime issue was fixed.
- Request handling passed with `1000` total requests, `850` valid successes, `0` degraded valid requests, `0` failed valid requests, `100` malformed 4xx rejections, and `50` oversized 4xx rejections.
- Full ORACLE stack preservation passed: detector fields were preserved, audit logging was recorded, and auth verification succeeded during controlled full-stack evaluation.
- `models_final` remained unchanged during final validation.

## Detection Results To Present

Use per-domain metrics. Do not claim one global perfect accuracy.

| Evaluation path | Accuracy | Precision | Recall | F1 | Presentation note |
| --- | ---: | ---: | ---: | ---: | --- |
| CIC production FusionEngine | `0.76 +/- 0.0196` | `1.0 +/- 0.0` | `0.52 +/- 0.0392` | `0.6833 +/- 0.0336` | Primary in-domain production path. |
| Historical mixed CIC/UNSW baseline | `0.7425` | `0.8173` | `0.6114` | `0.6995` | Historical MutantShield baseline only. |
| UNSW mapped path | `0.4622 +/- 0.0063` | `0.1217 +/- 0.0919` | `0.0133 +/- 0.0109` | `0.024 +/- 0.0194` | Weak mapped-schema generalization; not a final production claim. |
| CSE production baseline | `0.46 +/- 0.0189` | `0.0 +/- 0.0` | `0.0 +/- 0.0` | `0.0 +/- 0.0` | Honest baseline showing production weakness on this domain. |
| CSE repair candidate | `0.9689 +/- 0.0083` | `0.9733 +/- 0.0107` | `0.9645 +/- 0.0166` | `0.9687 +/- 0.0084` | Strong candidate-only result; not promoted production. |
| DoHBrw mapped path | `0.5 +/- 0.0` | `0.0 +/- 0.0` | `0.0 +/- 0.0` | `0.0 +/- 0.0` | Adapter required. |
| DoHBrw native adapter | `0.9 +/- 0.0283` | `0.8375 +/- 0.0392` | `0.9956 +/- 0.0063` | `0.9093 +/- 0.0241` | Strong native adapter result. |

## Full Stack Reliability Summary

- Field preservation: `1.0`
- Audit rate: `1.0`
- Auth rate: `1.0`
- Degraded/failed events in repeated proof: `0 / 0`
- Average p95 latency across repeated paths: `186.2068 ms`

## What Is Strong

- CIC production detection is usable but not perfect; final repeated recall is moderate.
- CSE can be adapted effectively with the repair candidate.
- DoHBrw requires and benefits from the native adapter.
- Oracle Core reliably preserves MutantShield detector output through assurance, ethics, audit, and response modules.

## What Is Weak

- UNSW mapped path is weak and should not be presented as a strong production claim.
- CSE production baseline is weak without the repair candidate.
- DoHBrw mapped-to-CIC path is not sufficient; the native adapter is required.

## Final Presentation Rule

Present ORACLE as a modular defensive framework with clear domain-specific detection behavior, reliable orchestration, auditability, safety controls, and candidate-only adaptation. Do not present a single global detection accuracy.
