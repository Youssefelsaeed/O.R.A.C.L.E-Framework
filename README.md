# O.R.A.C.L.E Framework

**Adaptive, quantum-aware cyber defense framework for detection, assurance, ethical decisioning, auditability, and secure response.**

O.R.A.C.L.E Framework is a modular cybersecurity platform that combines AI-assisted intrusion detection, token assurance, ethical response control, tamper-evident audit logging, secure response handling, candidate-only model evolution, and an operator dashboard.

Full title: **O.R.A.C.L.E Framework - Adaptive Quantum-Aware Cyber Defense**

## What It Is

O.R.A.C.L.E is designed as a defensive security framework for local deployment, validation, and extension. It normalizes security events, evaluates detection context, applies assurance and ethical governance, records auditable evidence, and coordinates response workflows through independent services.

The repository is packaged as a professional framework release. Raw datasets, secrets, virtual environments, cache files, generated reports, and heavyweight binary model artifacts are intentionally excluded from GitHub.

## Key Capabilities

- Multi-module security orchestration through Oracle Core.
- Ensemble-based traffic detection and candidate-only adaptation through MutantShield.
- Quantum-aware token assurance through QAuthCore.
- Ethical response governance through EthicQ.
- Tamper-evident security evidence through ChronoLedger.
- Secure response queueing through GhostTunnel.
- Native encrypted DNS behavioral anomaly support through DoHBrwAdapter.
- Operator visibility through Oracle GUI.
- Candidate-only Evolution Engine with adversarial hardening and promotion safety gates.

## Architecture Overview

Oracle Core receives normalized detection events and coordinates the runtime services:

- **Oracle Core**: Central orchestration API that normalizes detection events, calls assurance, ethics, audit, and response modules.
- **MutantShield**: AI detection engine using ensemble-based traffic analysis, candidate evolution, and domain adapters.
- **QAuthCore**: Token assurance and quantum-aware authentication service with async assurance mode.
- **EthicQ**: Ethical governance and decision policy engine for response control and human-review decisions.
- **ChronoLedger**: Tamper-evident audit ledger for security events, decisions, and retraining evidence.
- **GhostTunnel**: Secure response/transmission layer with fast-ack queueing and quantum-aware entropy support.
- **DoHBrwAdapter**: Native anomaly adapter for encrypted DNS-over-HTTPS behavioral detection.
- **Evolution Engine**: Candidate-only retraining and adversarial hardening pipeline with promotion safety gates.
- **Oracle Sensor**: Event and traffic simulation utilities for local validation.
- **Oracle GUI**: Operator dashboard for health, evolution state, performance, warnings, and reports.

## Quick Start

Use Python 3.12 on Windows PowerShell.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Install and build the GUI:

```powershell
cd O.R.A.C.L.E_GUi_V1_Figma
npm install
npm run build
cd ..
```

Run the full stack:

```powershell
python scripts/start_oracle_stack.py --gui --kill-existing
```

Open the dashboard:

```text
http://127.0.0.1:4173
```

Docker runtime quick start:

```powershell
python scripts/docker_oracle_up.py
python scripts/docker_oracle_status.py
```

Docker opens the same GUI at `http://127.0.0.1:4173`. Stop it with:

```powershell
python scripts/docker_oracle_down.py
```

Docker deployment is runtime-only. It excludes raw datasets, secrets, `node_modules`, generated reports, and model binaries from images; `models_final` is mounted read-only when present.

## Deployment

Local service ports:

- Oracle Core: `http://127.0.0.1:8000`
- QAuthCore: `http://127.0.0.1:8001`
- EthicQ: `http://127.0.0.1:8002`
- ChronoLedger: `http://127.0.0.1:8003`
- GhostTunnel: `http://127.0.0.1:8004`
- Oracle GUI: `http://127.0.0.1:4173`

See `docs/DEPLOYMENT.md` for setup, environment variables, health checks, and troubleshooting.

## Using The Framework

After opening `http://127.0.0.1:4173`, use the sidebar to navigate:

- **Global Dashboard**: overall backend health, latest events, live/replay status, and warnings.
- **MutantShield**: detection summary and candidate-safe actions.
- **Evolution Engine**: retraining/adaptation status with promotion safety controls.
- **QAuthCore**: assurance and token verification status.
- **EthicQ**: governance decisions and policy state.
- **ChronoLedger**: audit and chain verification status.
- **GhostTunnel**: secure response/queue status.
- **Settings**: configuration visibility and locked dangerous actions.

To demonstrate live-style event processing without packet capture permissions, run:

```powershell
python scripts/oracle_realtime_replay_proof.py --events 100
```

Then refresh the dashboard and latest-events panel.

## Evolution Engine And Adaptive Retraining

The Evolution Engine uses a candidate-only workflow. New model artifacts are written to candidate directories and are not promoted automatically. XGBoost and AutoEncoder candidate retraining are supported; LSTM/GNN retraining is contract-gated, while production inference remains active.

GAN synthetic generation is deferred to the roadmap. SIEM/SOAR/EDR integrations are also future external integrations.

## Security And Safety Controls

- `models_final` is protected and must not be modified during candidate evolution.
- Production promotion is blocked unless evaluation, adversarial, human approval, rollback, and hash-audit gates pass.
- ChronoLedger evidence is not trusted automatically for training; reviewed evidence is required.
- `.env`, secrets, raw datasets, virtual environments, cache files, generated reports, and `node_modules` are excluded from upload.

## Final Documentation

The public repository includes concise final documents:

- `docs/SRS_PROJECT_ORACLE.md`: final software requirements specification.
- `docs/ORACLE_FINAL_IMPORTANT_RESULTS.md`: concise real final results and presentation-safe metrics.
- `docs/ARCHITECTURE.md`: module architecture and runtime flow.
- `docs/DEPLOYMENT.md`: local and Docker deployment guide.
- `docs/USER_GUIDE.md`: operator usage guide.
- `docs/SECURITY_MODEL.md`: safety and security model.
- `docs/MODULE_CAPABILITIES.md`: module capability summary.
- `docs/RETRAINING_AND_EVOLUTION.md`: candidate-only adaptation workflow.

Dashboard and module pages mark values as `LIVE`, `REPORT`, `DEMO`, `LOCKED`, `LIVE/CONFIG`, or `LIVE SAFETY POLICY`.

Dashboard actions are live. Module actions are either live-safe or locked with a visible safety reason. Live network capture requires Scapy/Npcap/admin rights; realtime replay is the validated safe live proof when packet capture is unavailable.

## Operator Dashboard Preview

### Global Dashboard

![Global Dashboard](docs/assets/screenshots/Global%20Dashboard.png)

### MutantShield

![MutantShield](docs/assets/screenshots/Mutant%20Sheild.png)

### Evolution Engine

![Evolution Engine](docs/assets/screenshots/Evo%20Engine.png)

### QAuthCore

![QAuthCore](docs/assets/screenshots/QauthCore.png)

### EthicQ

![EthicQ](docs/assets/screenshots/EthicQ.png)

### ChronoLedger

![ChronoLedger](docs/assets/screenshots/ChronoLedger.png)

### GhostTunnel

![GhostTunnel](docs/assets/screenshots/GhostTunnel.png)

### Settings

![Settings](docs/assets/screenshots/Settings.png)

## Known Limitations

- Raw datasets are not included in the GitHub repository.
- Production model binaries may require local placement, Git LFS, or GitHub Release assets depending on deployment policy.
- Docker images do not include raw datasets or model binaries; runtime volumes are used instead.
- LSTM/GNN retraining is contract-gated; inference remains active.
- GAN synthetic generation is future work.
- SIEM/SOAR/EDR integrations are future work.
- Production deployment requires environment-specific hardening, secrets management, logging policy, and infrastructure review.

## Roadmap

Completed:

- Core framework.
- Oracle GUI.
- MutantShield detection.
- QAuthCore assurance.
- EthicQ governance.
- ChronoLedger audit.
- GhostTunnel secure response.
- Evolution Engine.
- CSE adaptation.
- DoHBrw anomaly adapter.
- Module capability validation.
- GitHub release.

Deferred/Future:

- GAN synthetic threat generation.
- LSTM/GNN candidate-safe retraining execution after contracts are satisfied.
- SIEM/SOAR/EDR integrations.
- Production deployment hardening.
- Cloud deployment.
- Container orchestration.

See `docs/ROADMAP.md`.

## Repository Structure

The repository contains runtime source, GUI source, deployment files, and concise final documentation. Development-only scripts, raw reports, datasets, local caches, and model binaries are intentionally excluded from the public scope.

## License / Usage Note

This repository is provided as a defensive cybersecurity research and framework implementation. Use it only in authorized environments. Review all model, dataset, and deployment assumptions before production use.
