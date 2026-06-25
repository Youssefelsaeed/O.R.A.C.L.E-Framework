# User Guide

O.R.A.C.L.E Framework is operated through local services and the Oracle GUI.

## Start The Framework

```powershell
python scripts/start_oracle_stack.py --gui --kill-existing
```

Open `http://127.0.0.1:4173`.

## Operator Dashboard

The Oracle GUI shows:

- Backend readiness
- Service health
- Async assurance status
- GhostTunnel queue state
- Evolution Engine status
- Promotion safety status
- Warnings and report links

## Basic Workflow

1. Start the stack.
2. Verify the dashboard reports ready services.
3. Submit or simulate events through Oracle Core or Oracle Sensor.
4. Review detection, assurance, ethics, audit, and response outcomes.
5. Use ChronoLedger evidence for traceability, not automatic training.

## Safety Rules

- Do not edit `models_final`.
- Do not promote candidates without approval and rollback planning.
- Do not train on unreviewed ChronoLedger evidence.
- Do not commit raw datasets, `.env`, secrets, reports, caches, or local model binaries.

The legacy detailed guide remains in `docs/ORACLE_USER_GUIDE.md`.
