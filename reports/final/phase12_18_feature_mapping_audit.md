# Phase 12.18 Feature Mapping Audit

## CIC-IDS2017
- Status: `PASS`
- Files discovered: 10
- Label column: ` Label`
- Average mapped ratio: `1.0`
- Zero-filled ratio: `0.0`
- Domain adapter required: `False`
- Note: CIC-style mapping is suitable for production MutantShield feature path.

## UNSW-NB15
- Status: `PASS`
- Files discovered: 10
- Label column: `label`
- Average mapped ratio: `0.5`
- Zero-filled ratio: `0.5`
- Domain adapter required: `True`
- Note: UNSW uses semantic mapping to CIC-style features; results must be reported as partial-domain transfer, not native CIC performance.

## CSE-CIC-IDS2018
- Status: `PASS`
- Files discovered: 10
- Label column: `Label`
- Average mapped ratio: `0.9872`
- Zero-filled ratio: `0.0128`
- Domain adapter required: `False`
- Note: CIC-style mapping is suitable for production MutantShield feature path.

## DoHBrw
- Status: `PASS`
- Files discovered: 10
- Label column: `Label`
- Average mapped ratio: `0.0`
- Zero-filled ratio: `1.0`
- Domain adapter required: `True`
- Note: DoHBrw is not a CICFlowMeter domain; native DoHBrwAdapter is required for truthful evaluation.

