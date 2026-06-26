# GUI Data Sources

The Oracle GUI labels major sections by source so operators can distinguish live backend state from saved validation evidence and static placeholders.

## Source Labels

- `LIVE`: Current backend endpoint or service health.
- `REPORT`: Saved validation or capability report.
- `LIVE/REPORT`: Live endpoint backed by a current or latest generated report.
- `LIVE/CONFIG`: Runtime configuration or scheduler state.
- `LIVE SAFETY POLICY`: Runtime safety policy enforced by disabled controls.
- `DEMO`: Static placeholder until live data stream is connected.

## Dashboard

- Backend status: `LIVE`
- Service health: `LIVE`
- Latest latency/status: `REPORT`
- Evolution metrics: `REPORT`
- Warnings: `LIVE/REPORT`
- Attack timeline: `DEMO`

## MutantShield

- Model load state: `REPORT` unless a dedicated live model endpoint is added.
- CSE/DoHBrw metrics: `REPORT`

## QAuthCore

- Health/token status: `LIVE` if service health endpoint is reachable.
- Capability metrics: `REPORT`

## ChronoLedger

- Health/chain status: `LIVE`
- Append/validation metrics: `REPORT`

## GhostTunnel

- Health/jobs: `LIVE/REPORT`
- Capability metrics: `REPORT`

## Evolution Engine

- Scheduler state: `LIVE/CONFIG`
- Candidates/metrics: `REPORT`
- Promotion controls: `LIVE SAFETY POLICY`

## Latest Events

Latest events are read from live proof reports and ChronoLedger/evolution evidence summaries. Realtime replay proof entries are labelled `LIVE_REPLAY`; live sensor fallback entries are labelled through the replay proof report.
