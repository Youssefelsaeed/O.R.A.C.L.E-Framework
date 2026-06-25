# GitHub Upload Guide

Repository name: `O.R.A.C.L.E-Framework`

Description: Adaptive quantum-aware cyber defense framework for detection, assurance, ethical decisioning, auditability, and secure response.

## Release Policy

The GitHub repository should contain the production-facing framework files only:

- Public README and run guide
- Professional docs
- Runtime source packages
- GUI source
- Runtime launcher scripts
- Release safety script

Do not upload generated reports, diagrams, raw datasets, phase-only testing scripts, development scripts, model binaries, secrets, virtual environments, caches, or `node_modules`.

## Safety Check

Run:

```powershell
python scripts/github_release_safety_check.py
```

Expected output:

```text
Safety Check: PASS
models_final unchanged: TRUE
```

## Recommended Safe Add

Stage only the intended production release paths:

```powershell
git add README.md RUN_ORACLE_FINAL.md GITHUB_RELEASE_NOTES_ORACLE_FINAL.md
git add .gitignore .env.example requirements.txt
git add docs/ARCHITECTURE.md docs/DEPLOYMENT.md docs/USER_GUIDE.md
git add docs/SECURITY_MODEL.md docs/TESTING_AND_VALIDATION.md docs/MODULE_CAPABILITIES.md
git add docs/RETRAINING_AND_EVOLUTION.md docs/API_REFERENCE.md docs/DATASETS.md
git add docs/ROADMAP.md docs/CONTRIBUTING.md docs/GITHUB_UPLOAD_GUIDE.md docs/REPOSITORY_STRUCTURE.md
git add scripts/start_oracle_stack.py scripts/oracle_stack_common.py scripts/check_services_health.py scripts/github_release_safety_check.py
git add oracle_core/ oracle_sensor/ mutantshield/
git add O.R.A.C.L.E_GUi_V1_Figma/
```

Then check:

```powershell
git status --short
```

## Push

If GitHub CLI is authenticated:

```powershell
gh repo create O.R.A.C.L.E-Framework --public --description "Adaptive quantum-aware cyber defense framework for detection, assurance, ethical decisioning, auditability, and secure response."
git push -u origin main
```

If GitHub CLI is unavailable, create the repository manually under `Youssefelsaeed`, add the remote URL, and push.
