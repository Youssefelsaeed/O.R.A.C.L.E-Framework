# Datasets

Raw datasets are not included in the GitHub repository.

## Local-Only Dataset Policy

Keep datasets under local-only paths such as `Workin with/`. The repository `.gitignore` excludes common raw dataset formats and dataset folders.

## Validated Dataset Families

- CIC/CICFlowMeter-style traffic for MutantShield production inference.
- CSE-CIC-IDS2018 attack distributions for candidate repair validation.
- DoHBrw / CIC-DoHBrw behavioral data for DoHBrwAdapter validation.
- UNSW-NB15 and CIC-IDS2017 as local validation sources.

## Upload Policy

Do not upload:

- Raw PCAP files
- Large CSV/parquet/feather/arff dataset files
- Local dataset folders
- Generated training buffers
- Human review queues containing operational evidence

Use documentation placeholders and instructions instead of uploading raw datasets.
