# O.R.A.C.L.E Framework Run Guide

Use these commands from the repository root on Windows PowerShell.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Build GUI

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

## Health

```powershell
python scripts/oracle_final_acceptance_test.py
```

## Full Validation

```powershell
python scripts/oracle_phase12_11_module_capability_validation.py
```

## Final Benchmark

```powershell
python scripts/oracle_phase11_final_benchmark.py
```

## Safety Notes

- Do not edit or overwrite `models_final`.
- Do not commit `.env`, secrets, raw datasets, `node_modules`, virtual environments, cache files, reports, or temporary files.
- GAN generation and SIEM/SOAR/EDR integrations remain roadmap items.
