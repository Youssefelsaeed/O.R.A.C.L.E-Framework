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
See `docs/DOCKER_DEPLOYMENT_ARCHITECTURE.md` for Docker runtime architecture.

## Running Tests And Benchmarks

Operator-safe validation uses the existing running stack and does not stop services it did not start:

Health and acceptance:

```powershell
python scripts/oracle_final_acceptance_test.py
```

Full module validation:

```powershell
python scripts/oracle_runtime_current_code_check.py
```

Final benchmark:

```powershell
python scripts/oracle_final_acceptance_test.py
```

Live operator proof:

```powershell
python scripts/oracle_live_sensor_smoke_test.py
python scripts/oracle_realtime_replay_proof.py --events 100
```

Use `--manage-stack` only when you intentionally want a validation script to start and stop its own backend services.

GUI live demo validation:

```powershell
python scripts/oracle_runtime_current_code_check.py
python scripts/oracle_realtime_replay_proof.py --events 25
```

Docker runtime validation:

```powershell
python scripts/docker_oracle_status.py
```

Final operational verification:

```powershell
python scripts/oracle_runtime_current_code_check.py
python scripts/oracle_final_acceptance_test.py
```

This verifies that the current Oracle Core runtime is loaded, the stack is reachable, and the final operator acceptance path is available.

Final controlled detection verification:

```powershell
python scripts/oracle_runtime_current_code_check.py
```

Phase 12.20 is the current evidence gate for detection claims. `/oracle/runtime-info` must return `runtime_marker: phase12_19_current_runtime` before full-stack detection or request-handling metrics are trusted.

Final metric summaries:

- Historical mixed CIC/UNSW MutantShield baseline: accuracy `0.7425`, precision `0.8173`, recall `0.6114`, F1 `0.6995`. This is historical validation evidence, not a full-stack runtime claim.
- Phase 12.20 repeated standalone highlights: CIC production recall `0.52 +/- 0.0392`, CSE production recall `0.0 +/- 0.0`, CSE repair candidate recall `0.9645 +/- 0.0166`, DoHBrw mapped recall `0.0 +/- 0.0`, DoHBrw native adapter recall `0.9956 +/- 0.0063`.
- Phase 12.20 full-stack proof: repeated runs preserved detector fields with audit/auth rates of `1.0` and no degraded/failed events. See `docs/ORACLE_FULL_STACK_FINAL_DETECTION_PROOF.md`.

Use `docs/ORACLE_PRESENTATION_METRICS_FINAL.md` and `docs/ORACLE_FINAL_DETECTION_CONFIDENCE_VERDICT.md` for presentation numbers. Do not claim one global perfect accuracy.

The live dashboard demo flow is documented in `docs/ORACLE_GUI_LIVE_DEMO_SCRIPT.md`.

## Evolution Engine And Adaptive Retraining

The Evolution Engine uses a candidate-only workflow. New model artifacts are written to candidate directories and are not promoted automatically. XGBoost and AutoEncoder candidate retraining are supported; LSTM/GNN retraining is contract-gated, while production inference remains active.

GAN synthetic generation is deferred to the roadmap. SIEM/SOAR/EDR integrations are also future external integrations.

## Security And Safety Controls

- `models_final` is protected and must not be modified during candidate evolution.
- Production promotion is blocked unless evaluation, adversarial, human approval, rollback, and hash-audit gates pass.
- ChronoLedger evidence is not trusted automatically for training; reviewed evidence is required.
- `.env`, secrets, raw datasets, virtual environments, cache files, generated reports, and `node_modules` are excluded from upload.

## Reports And Validation Results

Current validated framework status:

- `ORACLE_MODULE_CAPABILITY_VALIDATED`
- `ORACLE_FULLY_TESTED_AND_READY`
- `ORACLE_FINAL_QA_COMPLETE`
- `ORACLE_FINAL_DETECTION_CONFIDENCE_VERIFIED` after Phase 12.20 verification passes

Summary metrics are documented in `docs/ORACLE_PRESENTATION_METRICS_FINAL.md`, `docs/ORACLE_MUTANTSHIELD_FINAL_DETECTION_RESULTS.md`, and `docs/ORACLE_FULL_STACK_FINAL_DETECTION_PROOF.md`.

Phase 12.20 detection truth uses repeated fixed-seed evidence instead of banner metrics. It separates Production FusionEngine, UNSW mapped validation, CSE production baseline, CSE repair candidate, DoHBrw mapped baseline, DoHBrw native adapter, and full ORACLE stack preservation/audit behavior.

Latest Phase 12.20 verification confirms that some mapped/production baselines still produce `0.0` recall, while the CSE repair candidate and DoHBrw native adapter perform well on repeated controlled samples. Banner/global detection metrics should be replaced by the per-path mean +/- std tables in `docs/ORACLE_PRESENTATION_METRICS_FINAL.md`.

Dashboard and module pages mark values as `LIVE`, `REPORT`, `DEMO`, `LOCKED`, `LIVE/CONFIG`, or `LIVE SAFETY POLICY`.

Dashboard actions are live. Module actions are either live-safe or locked with a visible safety reason. Live network capture requires Scapy/Npcap/admin rights; realtime replay is the validated safe live proof when packet capture is unavailable.

## Operator Dashboard Preview

Selected professional screenshots can be added when available:

- `docs/assets/screenshots/dashboard.png`
- `docs/assets/screenshots/latest_events.png`
- `docs/assets/screenshots/evolution_engine.png`
- `docs/assets/screenshots/mutantshield.png`

No screenshot links are embedded here until those exact files exist, to avoid broken README images.

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

See `docs/ROADMAP.md` and `docs/SIEM_SOAR_EDR_INTEGRATION.md`.

## Repository Structure

See `docs/REPOSITORY_STRUCTURE.md` for the professional repository map. Some internal folder names reflect development history, but public entrypoints are documented through the files in `docs/`.

## License / Usage Note

This repository is provided as a defensive cybersecurity research and framework implementation. Use it only in authorized environments. Review all model, dataset, and deployment assumptions before production use.
