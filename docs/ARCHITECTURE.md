# O.R.A.C.L.E Framework Architecture

O.R.A.C.L.E Framework is organized as a modular defensive security platform. Oracle Core acts as the central orchestration API and coordinates specialized services for detection, assurance, ethical decisioning, auditability, and secure response.

## Runtime Flow

1. Oracle Sensor or an external source submits a normalized event to Oracle Core.
2. Oracle Core validates and normalizes the payload.
3. MutantShield evaluates traffic and adapter-specific detection context.
4. QAuthCore provides token assurance and asynchronous assurance state.
5. EthicQ applies response-governance policy and human-review rules.
6. ChronoLedger records tamper-evident evidence.
7. GhostTunnel handles secure response/transmission jobs.
8. Oracle GUI exposes health, readiness, warnings, evolution state, and operational summaries.

## Core Components

- **Oracle Core**: Central orchestration API that normalizes detection events, calls assurance, ethics, audit, and response modules.
- **MutantShield**: AI detection engine using ensemble-based traffic analysis, candidate evolution, and domain adapters.
- **QAuthCore**: Token assurance and quantum-aware authentication service with async assurance mode.
- **EthicQ**: Ethical governance and decision policy engine for response control and human-review decisions.
- **ChronoLedger**: Tamper-evident audit ledger for security events, decisions, and retraining evidence.
- **GhostTunnel**: Secure response/transmission layer with fast-ack queueing and quantum-aware entropy support.
- **DoHBrwAdapter**: Native anomaly adapter for encrypted DNS-over-HTTPS behavioral detection.
- **Evolution Engine**: Candidate-only retraining and adversarial hardening pipeline with promotion safety gates.
- **Oracle GUI**: Operator dashboard for health, evolution state, performance, warnings, and reports.

## Extension Points

New detection domains should be added as adapters. New response integrations should use the same assurance, ethics, audit, and promotion-safety controls rather than bypassing Oracle Core.

Detailed historical architecture notes remain in `docs/ORACLE_ARCHITECTURE.md`.
