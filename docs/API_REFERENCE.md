# API Reference

Oracle Core is the primary integration point for O.R.A.C.L.E Framework.

## Oracle Core

Common local endpoints:

- `GET /health`
- `GET /oracle/test`
- `POST /oracle/process`
- `GET /oracle/dashboard/summary`
- `GET /oracle/dashboard/health`
- `GET /oracle/dashboard/evolution`

## Event Processing

`POST /oracle/process` accepts normalized security events and coordinates detection, assurance, ethics, audit, and response behavior.

## Dashboard API

Dashboard endpoints are consumed by Oracle GUI and expose backend readiness, service state, evolution status, warnings, and safety posture.

## Service Ports

- Oracle Core: `8000`
- QAuthCore: `8001`
- EthicQ: `8002`
- ChronoLedger: `8003`
- GhostTunnel: `8004`

Production API exposure should add authentication, TLS, network segmentation, and environment-specific access controls.
