# Final Manual Validation Guide

This guide is for the final operator validation of O.R.A.C.L.E Framework. It does not add runtime features or modify model artifacts.

## 1. Start The Stack

Run from the repository root:

```powershell
python scripts/start_oracle_stack.py --gui --kill-existing
```

## 2. Open The GUI

```text
http://127.0.0.1:4173
```

## 3. Verify Dashboard State

Confirm the dashboard shows:

- Backend `READY`
- Async Quantum Assurance `ACTIVE`
- GhostTunnel Fast-Ack `ACTIVE`
- Evolution `READY`
- Promotion `BLOCKED_SAFE`

## 4. Visit Operator Pages

Capture or visually verify these GUI areas:

- Dashboard
- MutantShield
- QAuthCore
- EthicQ
- ChronoLedger
- GhostTunnel
- Evolution Engine
- Settings / Safety Controls

## 5. Run Final Tests

The final validation scripts default to operator mode. They use the existing running stack and do not stop services they did not start.

Run:

```powershell
python scripts/oracle_phase12_17_final_operational_verification.py
python scripts/oracle_final_acceptance_test.py
python scripts/oracle_phase12_11_module_capability_validation.py
```

Expected status:

```text
ORACLE_FINAL_READY
ORACLE_MODULE_CAPABILITY_VALIDATED
ORACLE_FINAL_OPERATIONALLY_VERIFIED
models_final unchanged: TRUE
```

Phase 12.17 performs the final operational loop: stack boot and three-minute stability, backend endpoint coverage, GUI action verification, 1000 mixed `/oracle/process` requests across concurrency levels, live replay latest-events freshness, reports/docs checks, issue sweep, GitHub safety, and final acceptance.

If the stack is not already running, start it manually or use managed test mode explicitly:

```powershell
python scripts/oracle_final_acceptance_test.py --manage-stack
python scripts/oracle_phase12_11_module_capability_validation.py --manage-stack
```

Use `--kill-existing` only with `--manage-stack`.

## 6. Run Live Operator Proofs

Run:

```powershell
python scripts/oracle_operator_final_validation.py
python scripts/check_live_sensor_readiness.py
python scripts/test_module_gui_actions.py
python scripts/test_module_pages_operator_ui.py
python scripts/oracle_live_sensor_smoke_test.py
python scripts/oracle_realtime_replay_proof.py --events 100
```

The live sensor smoke test attempts limited packet capture. If packet capture permissions, Scapy, or Npcap are unavailable, it reports the blocked reason and uses realtime replay proof as a safe fallback.

Confirm the GUI monitoring mode is truthful:

- `Live Network Capture`: `ACTIVE` only if sensor readiness passes and live capture is running.
- `Realtime Replay`: `LAST RUN` or `ACTIVE` after `oracle_realtime_replay_proof.py`.
- `Latest Event Source`: `LIVE_REPLAY`, `LIVE_SENSOR`, or `REPORT`.
- If Scapy/Npcap/admin permissions are unavailable, the GUI must say live network capture is not active.

Module-page buttons must never silently do nothing. They either run a safe backend action or open a visible locked/safety action result explaining why destructive behavior is blocked.

## 7. Capture Screenshots

Save screenshots using these exact filenames:

- `docs/assets/screenshots/dashboard.png`
- `docs/assets/screenshots/mutantshield.png`
- `docs/assets/screenshots/qauthcore.png`
- `docs/assets/screenshots/ethicq.png`
- `docs/assets/screenshots/chronoledger.png`
- `docs/assets/screenshots/ghosttunnel.png`
- `docs/assets/screenshots/evolution_engine.png`
- `docs/assets/screenshots/settings_safety.png`
- `docs/assets/screenshots/final_acceptance_console.png`

Do not include screenshots containing secrets, private local paths, API keys, tokens, `.env` values, raw datasets, or personal credentials.

## 8. Final Manual Validation Status

After completing the checklist and adding screenshots, the final presentation status is:

```text
ORACLE_FINAL_MANUALLY_VALIDATED
```

If screenshots are not present yet, the repository remains ready for presentation and QA, and screenshots can be added after local execution.
