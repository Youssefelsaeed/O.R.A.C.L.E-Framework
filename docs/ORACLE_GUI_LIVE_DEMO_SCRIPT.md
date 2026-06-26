# ORACLE GUI Live Demo Script

This script demonstrates that the GUI is connected to the live Oracle backend and can show newly processed events.

## 1. Start The Stack

```powershell
python scripts/start_oracle_stack.py --gui --kill-existing
```

Open:

```text
http://127.0.0.1:4173
```

The dashboard should show:

- `Data Mode: LIVE BACKEND CONNECTED`
- API base: `http://127.0.0.1:8000`
- Backend status and service health labelled `LIVE`

## 2. Click Dashboard Actions

Click:

- `Health Check`
- `Run Validation`

The `Action Result` panel should show:

- action name
- success or failure status
- timestamp
- JSON preview from the backend

If an endpoint fails, the error is shown in the dashboard instead of being hidden.

## 3. Generate Live Replay Events

In a terminal:

```powershell
python scripts/oracle_realtime_replay_proof.py --events 25
```

Then click:

- `Refresh`
- `Refresh Events`

The `Latest ORACLE Events - LIVE` table should display rows with:

- timestamp
- oracle_trace_id
- flow_id
- risk_label
- attack_family
- final_action
- audit_logged
- data_source

Rows with `LIVE_REPLAY` prove that the GUI is showing events generated during the current operator session.

## 4. Show Backend Proof

Open this backend URL in a browser tab:

```text
http://127.0.0.1:8000/oracle/dashboard/latest-events
```

Compare the `LIVE_REPLAY` rows and trace IDs with the GUI table.

## 5. Explain Data Badges

- `LIVE`: current backend endpoint or current service state.
- `REPORT DATA`: saved validation/capability evidence.
- `DEMO VISUAL`: decorative placeholder only.
- `LIVE/REPORT`: live endpoint backed by latest generated reports.
- `LIVE SAFETY POLICY`: disabled or blocked action controlled by ORACLE safety policy.

No dashboard section should silently show mock data.

## 6. Validate The Demo Setup

```powershell
python scripts/test_dashboard_action_endpoints.py
python scripts/test_gui_operator_console_live.py
```

Build the GUI:

```powershell
cd O.R.A.C.L.E_GUi_V1_Figma
npm run build
```

## Troubleshooting

- If the dashboard says backend offline, verify `http://127.0.0.1:8000/oracle/dashboard/summary`.
- If the latest events table is empty, run `python scripts/oracle_realtime_replay_proof.py --events 25`.
- If buttons appear to do nothing, check the `Action Result` panel for HTTP errors.
- If report links fail, verify `http://127.0.0.1:8000/oracle/dashboard/reports`.
