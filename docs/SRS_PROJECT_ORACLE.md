# Software Requirements Specification: Project O.R.A.C.L.E

## 1. Introduction

Project O.R.A.C.L.E is a modular defensive cybersecurity framework that combines detection, orchestration, assurance, ethical decisioning, auditability, secure response handling, candidate-only adaptation, and an operator-facing GUI.

The system was developed as a final framework demonstration and research implementation. It is intended for authorized local deployment, academic presentation, and controlled extension.

## 2. Purpose

This SRS defines the final requirements for ORACLE from initial concept through the final validated framework:

- Detect suspicious network-flow events through MutantShield and supported adapters.
- Orchestrate detection outputs through Oracle Core.
- Verify assurance through QAuthCore.
- Apply ethical governance through EthicQ.
- Store tamper-evident evidence through ChronoLedger.
- Route secure response jobs through GhostTunnel.
- Present operator status through the Oracle GUI.
- Support candidate-only model evolution without modifying production models.

## 3. Scope

Included in the final release:

- Oracle Core API and dashboard endpoints.
- MutantShield production inference and candidate/adaptor support.
- QAuthCore, EthicQ, ChronoLedger, and GhostTunnel runtime services.
- Oracle Sensor replay/simulation utilities.
- Oracle GUI for operator navigation and demonstration.
- Docker/local runtime deployment files.
- Documentation for architecture, deployment, usage, security, retraining, testing, and roadmap.

Out of scope for the final release:

- Raw datasets in GitHub.
- Model binaries in normal Git history.
- GAN training.
- SIEM/SOAR/EDR production integration.
- Automatic model promotion.
- Unreviewed production deployment.

## 4. System Overview

ORACLE receives normalized detection events and processes them through a governed pipeline:

1. A flow or replayed event is evaluated by MutantShield or an adapter.
2. Oracle Core validates and normalizes the event.
3. QAuthCore verifies assurance.
4. EthicQ decides whether the response is allowed, blocked, or requires review.
5. ChronoLedger records audit evidence.
6. GhostTunnel handles secure response acknowledgement.
7. Oracle GUI displays module status, latest events, safety state, and operator actions.

## 5. Users

- **Operator**: Starts the stack, opens the GUI, checks module status, and demonstrates event processing.
- **Security analyst**: Reviews detection outputs, latest events, audit records, warnings, and module status.
- **ML engineer**: Reviews candidate-only adaptation results and feature/generalization behavior.
- **Governance reviewer**: Confirms promotion safety, ethical controls, and audit requirements.

## 6. Functional Requirements

### 6.1 Oracle Core

- Shall expose `/oracle/process` for normalized detection events.
- Shall reject malformed and oversized payloads with structured 4xx responses.
- Shall expose health, dashboard summary, latest events, reports, and runtime-info endpoints.
- Shall preserve detector fields including risk score, risk label, attack family, detector source, and dataset source.

### 6.2 MutantShield

- Shall provide production FusionEngine inference for CIC-style flow features.
- Shall support mapped validation paths for external datasets with documented limitations.
- Shall support candidate-only repair/adaptation paths without promoting candidates automatically.
- Shall preserve production model immutability.

### 6.3 QAuthCore

- Shall issue and verify assurance tokens.
- Shall expose service health and verification behavior usable by Oracle Core.
- Shall support runtime throughput through bounded caching where configured.

### 6.4 EthicQ

- Shall evaluate response policy and produce governance decisions.
- Shall prevent unsafe actions from being treated as automatic approvals.
- Shall keep human-review paths visible.

### 6.5 ChronoLedger

- Shall log processed events and verification evidence.
- Shall expose chain health/verification state.
- Shall support auditability without treating evidence as automatically reviewed training data.

### 6.6 GhostTunnel

- Shall acknowledge secure response jobs.
- Shall expose queue/job state.
- Shall avoid blocking Oracle Core on noncritical response delivery.

### 6.7 Oracle GUI

- Shall display service health, dashboard status, latest events, data source labels, warnings, module pages, and safe operator actions.
- Shall distinguish live backend data from reports, demo visuals, and locked actions.
- Shall show clear errors instead of silent button failures.

## 7. Non-Functional Requirements

- The framework shall be runnable locally from documented commands.
- Runtime behavior shall be demonstrable through the GUI.
- Public GitHub contents shall exclude raw datasets, secrets, generated reports, local caches, node_modules, and model binaries.
- Documentation shall be clear enough for a new user to deploy and navigate the system.
- Final metrics shall be presented honestly per dataset/path and not as one global perfect score.

## 8. Security And Safety Requirements

- `models_final` shall not be modified during evaluation, documentation, or candidate testing.
- Candidate outputs shall not imply production promotion.
- GUI dangerous actions shall be locked or explained.
- `.env`, secrets, raw datasets, and local model binaries shall not be committed.
- SIEM/SOAR/EDR actions remain future integrations and must not bypass Oracle safety controls.

## 9. Data Requirements

Final evaluation used local datasets only:

- CIC-IDS2017 for in-domain production behavior.
- UNSW-NB15 for mapped-schema generalization.
- CSE-CIC-IDS2018 for partial generalization and repair candidate behavior.
- DoHBrw for encrypted DNS anomaly adapter behavior.

These datasets are not included in GitHub.

## 10. Acceptance Criteria

The final framework is accepted when:

- Local runtime starts successfully.
- `/oracle/runtime-info` proves current code.
- GUI opens and shows live backend state.
- Oracle Core preserves detector outputs through the full stack.
- QAuthCore, EthicQ, ChronoLedger, and GhostTunnel are reachable.
- Request handling rejects malformed/oversized requests safely.
- `models_final` remains unchanged.
- GitHub contains only the professional runtime framework, user docs, screenshots, and final summary documentation.

## 11. Final Limitations

- Real network deployment still requires environment calibration and monitoring.
- Dataset replay is not a guarantee of performance on a new live network.
- UNSW mapped path is weak and should not be presented as native production readiness.
- CSE repair candidate is candidate-only unless separately promoted by a controlled process.
- DoHBrw requires the native adapter; mapped CIC-style features are insufficient.
- GAN and SIEM/SOAR/EDR remain future work.
