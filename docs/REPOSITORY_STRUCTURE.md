# Repository Structure

This repository is presented as a professional framework package. Some internal folder names may reflect development history, but public entrypoints are documented here.

## Public Entrypoints

- `README.md`: Framework overview and quick start.
- `RUN_ORACLE_FINAL.md`: Local run commands.
- `docs/`: Professional documentation entrypoints.
- `scripts/start_oracle_stack.py`: Runtime stack launcher.
- `oracle_core/`: Central orchestration API.
- `oracle_sensor/`: Event and traffic simulation helpers.
- `mutantshield/`: Evolution Engine, adapters, mapping, contracts, and detection support package.
- `O.R.A.C.L.E_GUi_V1_Figma/`: Oracle GUI source.

## Runtime Services

Runtime service implementations include Oracle Core, QAuthCore, EthicQ, ChronoLedger, GhostTunnel, MutantShield, and Oracle Sensor. Some service source folders are retained locally under historical names, but the documented product components use the clean names in this guide.

## AI Detection Engine

MutantShield provides ensemble detection support, candidate-only evolution, feature mapping, adversarial hardening, contracts, and domain adapters including DoHBrwAdapter.

## GUI

Oracle GUI is a React/Vite operator dashboard for health, evolution state, performance, warnings, and report visibility.

## Scripts

The GitHub release should include runtime and release-safety scripts only. Development phase scripts, generated test scripts, and one-off research scripts should remain local unless intentionally published later.

## Reports

Generated reports are local evidence and are not uploaded in the production release. Professional summary metrics are documented in `docs/TESTING_AND_VALIDATION.md` and `docs/MODULE_CAPABILITIES.md`.

## Models

Model binaries should stay out of normal Git history. Use local provisioning, Git LFS, or GitHub Release assets if redistribution is approved.

## Datasets

Datasets are local-only. Do not upload raw datasets or generated training buffers.
