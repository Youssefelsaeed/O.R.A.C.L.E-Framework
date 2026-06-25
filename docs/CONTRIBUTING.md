# Contributing

Contributions should preserve O.R.A.C.L.E Framework safety boundaries.

## Rules

- Do not commit `.env`, secrets, raw datasets, virtual environments, cache files, generated reports, or `node_modules`.
- Do not modify `models_final` without explicit approval and hash-audit evidence.
- Do not bypass Oracle Core when adding new assurance, ethics, audit, or response behavior.
- Add adapters for new detection domains instead of weakening existing schemas.
- Keep promotion blocked unless all safety gates pass.

## Suggested Contribution Areas

- Production deployment hardening.
- Additional domain adapters.
- API documentation.
- GUI operator improvements.
- SIEM/SOAR/EDR connectors as optional integrations.
- Quality-gated synthetic data tooling.
