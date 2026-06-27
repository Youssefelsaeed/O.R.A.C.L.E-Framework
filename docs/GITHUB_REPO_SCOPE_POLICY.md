# GitHub Repository Scope Policy

The public ORACLE repository is scoped as a professional runtime framework, not a local research scratchpad.

## Keep
- Runtime source for Oracle Core, QAuthCore, EthicQ, ChronoLedger, GhostTunnel, Oracle Sensor, MutantShield, and the GUI.
- Deployment files, Docker files, requirements, README, and core operator scripts.
- Professional docs for architecture, deployment, usage, security, testing, capabilities, retraining, roadmap, GUI demo, and final metrics truth.

## Do Not Track
- Raw datasets, model binaries, candidate model artifacts, local logs, caches, generated CSV/parquet files, and private eval outputs.
- Phase scripts, temporary benchmarks, raw JSON reports, and old experimental notes unless they are explicitly part of the final runtime workflow.

## Latest Audit
- Generated at: `2026-06-27T14:47:08Z`
- Tracked files audited: `198`
- Recommended removals: `0`

Files removed from tracking are not deleted locally; cleanup uses `git rm --cached` only.
