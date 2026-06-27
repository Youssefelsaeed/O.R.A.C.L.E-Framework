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

## Docker Runtime Deployment

Docker deployment starts the same runtime services without changing the local Python startup scripts.

Requirements:

- Docker Desktop or Linux Docker engine
- Linux containers enabled on Docker Desktop

Start:

```powershell
python scripts/docker_oracle_up.py
```

Open:

```text
http://127.0.0.1:4173
```

Validate:

```powershell
python scripts/docker_oracle_status.py
```

Stop:

```powershell
python scripts/docker_oracle_down.py
```

Docker is runtime deployment, not training deployment. Raw datasets are excluded from images. `models_final` is mounted read-only when present, `models_candidate` is mounted read/write, and realtime replay proof works against Dockerized Oracle Core. Live packet capture remains host/manual because it depends on Scapy, Npcap, and permissions.

## Health And Validation

Operator mode uses the running stack and leaves it alive:

```powershell
python scripts/oracle_final_acceptance_test.py
python scripts/oracle_runtime_current_code_check.py
```

Managed test mode is explicit:

```powershell
python scripts/oracle_final_acceptance_test.py --manage-stack
```

Run live proof:

```powershell
python scripts/oracle_live_sensor_smoke_test.py
python scripts/oracle_realtime_replay_proof.py --events 100
```

Run the final operational verification loop:

```powershell
python scripts/oracle_runtime_current_code_check.py
python scripts/oracle_final_acceptance_test.py
```

This verifies current-code runtime proof, service reachability, and final acceptance without requiring development phase scripts.

If GUI buttons do not respond, verify `VITE_ORACLE_API_BASE_URL=http://127.0.0.1:8000`, rebuild the GUI, and confirm `http://127.0.0.1:8000/oracle/dashboard/summary` is reachable.

## Deployment Notes

- Do not commit `.env`; use `.env.example` as a template.
- Keep raw datasets local.
- Keep model binaries out of normal Git history unless Git LFS or release assets are intentionally used.
- Production deployment requires environment-specific TLS, secret management, logging retention, access control, and monitoring.

Detailed deployment history remains in `docs/ORACLE_DEPLOYMENT_GUIDE.md`.
