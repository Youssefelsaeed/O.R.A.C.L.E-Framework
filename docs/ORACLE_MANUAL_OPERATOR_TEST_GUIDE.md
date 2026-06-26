# ORACLE Manual Operator Test Guide

1. Open terminal in the project root.
2. Activate environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Start backend + GUI:

```powershell
python scripts/start_oracle_stack.py --gui --kill-existing
```

4. Open GUI:

```text
http://127.0.0.1:4173
```

5. Verify dashboard:

- Backend READY
- Async Assurance ACTIVE
- GhostTunnel ACTIVE
- Evolution READY
- Promotion BLOCKED_SAFE

6. Run operator-safe final validation. These scripts use the existing running stack and do not stop services they did not start:

```powershell
python scripts/oracle_final_acceptance_test.py
python scripts/oracle_phase12_11_module_capability_validation.py
```

7. Run live operator proof:

```powershell
python scripts/oracle_operator_final_validation.py
python scripts/oracle_live_sensor_smoke_test.py
python scripts/oracle_realtime_replay_proof.py --events 100
```

8. Run final benchmark:

```powershell
python scripts/oracle_phase11_final_benchmark.py
```

9. Managed test mode is optional and explicit:

```powershell
python scripts/oracle_final_acceptance_test.py --manage-stack
```

## Screenshots To Capture

- Dashboard
- Evolution page
- MutantShield page
- ChronoLedger page
- Final benchmark console
- Final operator validation console
- Realtime replay proof console

## Data Source Labels

The GUI labels major sections as `LIVE`, `REPORT`, `DEMO`, `LIVE/CONFIG`, or `LIVE SAFETY POLICY`. See `docs/GUI_DATA_SOURCES.md`.
