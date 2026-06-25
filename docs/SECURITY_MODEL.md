# Security Model

O.R.A.C.L.E Framework is designed for defensive security research and controlled deployment.

## Safety Principles

- Production model artifacts are protected.
- Candidate training does not overwrite `models_final`.
- Promotion is blocked unless evaluation, adversarial, human approval, rollback, and hash-audit gates pass.
- ChronoLedger evidence is auditable evidence, not automatically trusted training data.
- Secrets, `.env`, raw datasets, virtual environments, cache files, and generated reports are excluded from GitHub.

## Security Boundaries

- Oracle Core validates and normalizes incoming events.
- QAuthCore provides token assurance and asynchronous assurance state.
- EthicQ controls response decisions and human-review outcomes.
- ChronoLedger records decisions and evidence.
- GhostTunnel handles response/transmission jobs with queue visibility.

## Deployment Hardening

Production deployment should add environment-specific controls:

- TLS termination
- Authentication and authorization policy
- Secret management
- Log retention and privacy policy
- Network segmentation
- Monitoring and alerting
- Backup and rollback procedures

Detailed historical safety documentation remains in `docs/ORACLE_SECURITY_SAFETY_MODEL.md`.
