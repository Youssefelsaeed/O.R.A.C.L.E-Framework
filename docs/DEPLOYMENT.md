# Deployment

This guide covers local Windows deployment for O.R.A.C.L.E Framework.

## Requirements

- Python 3.12
- Node.js and npm for Oracle GUI
- PowerShell
- Local model artifacts provisioned outside normal Git history when required

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## GUI Setup

```powershell
cd O.R.A.C.L.E_GUi_V1_Figma
npm install
npm run build
cd ..
```

## Run Full Stack

```powershell
python scripts/start_oracle_stack.py --gui --kill-existing
```

Open:

```text
http://127.0.0.1:4173
```

## Service Ports

- Oracle Core: `8000`
- QAuthCore: `8001`
- EthicQ: `8002`
- ChronoLedger: `8003`
- GhostTunnel: `8004`
- Oracle GUI: `4173`

## Health And Validation

Operator mode uses the running stack and leaves it alive:

```powershell
python scripts/oracle_final_acceptance_test.py
python scripts/oracle_phase12_11_module_capability_validation.py
python scripts/oracle_phase11_final_benchmark.py
```

Managed test mode is explicit:

```powershell
python scripts/oracle_final_acceptance_test.py --manage-stack
python scripts/oracle_phase12_11_module_capability_validation.py --manage-stack
```

Run live proof:

```powershell
python scripts/oracle_live_sensor_smoke_test.py
python scripts/oracle_realtime_replay_proof.py --events 100
```

If GUI buttons do not respond, verify `VITE_ORACLE_API_BASE_URL=http://127.0.0.1:8000`, rebuild the GUI, and confirm `http://127.0.0.1:8000/oracle/dashboard/summary` is reachable.

## Deployment Notes

- Do not commit `.env`; use `.env.example` as a template.
- Keep raw datasets local.
- Keep model binaries out of normal Git history unless Git LFS or release assets are intentionally used.
- Production deployment requires environment-specific TLS, secret management, logging retention, access control, and monitoring.

Detailed deployment history remains in `docs/ORACLE_DEPLOYMENT_GUIDE.md`.
