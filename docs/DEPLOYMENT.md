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

```powershell
python scripts/oracle_final_acceptance_test.py
python scripts/oracle_phase12_11_module_capability_validation.py
python scripts/oracle_phase11_final_benchmark.py
```

## Deployment Notes

- Do not commit `.env`; use `.env.example` as a template.
- Keep raw datasets local.
- Keep model binaries out of normal Git history unless Git LFS or release assets are intentionally used.
- Production deployment requires environment-specific TLS, secret management, logging retention, access control, and monitoring.

Detailed deployment history remains in `docs/ORACLE_DEPLOYMENT_GUIDE.md`.
