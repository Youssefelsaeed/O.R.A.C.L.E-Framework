# MutantShield Runtime Ensemble Proof

Final status: `MUTANTSHIELD_ENSEMBLE_RUNTIME_VERIFIED`

This proof verifies runtime inference only. It does not train models, tune thresholds, promote candidates, edit `models_final`, or fabricate model outputs.

## Direct Answer

- XGBoost is active during detection.
- AutoEncoder is active during detection.
- LSTM is active during detection.
- GNN is active during detection, with conservative fallback on the first row before graph history exists.
- FusionMLP is active; weighted fusion fallback was not used in the verified run.
- LSTM and GNN are blocked only for candidate retraining. Their production inference artifacts load and execute.
- Oracle Core receives and preserves fused MutantShield output.
- `models_final` was unchanged before and after the proof.

## Model Load Proof

| Component | Runtime Status | Evidence |
| --- | --- | --- |
| XGBoost | `ACTIVE` | `xgboost_classifier.pkl` path exists and `FusionEngineV2.xgb_model` loaded. |
| AutoEncoder | `ACTIVE` | `autoencoder_v1.pkl` path exists and `FusionEngineV2.ae_model` loaded. |
| LSTM | `ACTIVE` | LSTM weights, metadata, scaler, feature names, and model loaded. |
| GNN | `ACTIVE_WITH_FALLBACK` | GNN model and builder loaded; first row used conservative fallback because no graph history existed yet, later rows used dynamic graph output. |
| FusionMLP | `ACTIVE` | `learned_fusion_mlp.pt` loaded and runtime mode was `FUSION_MLP`. |
| Risk calibrator | `ACTIVE` | `risk_calibrator.pkl` loaded. |

Retraining classification:

| Component | Runtime Inference | Candidate Retraining |
| --- | --- | --- |
| XGBoost | `ACTIVE` | `RETRAINABLE` |
| AutoEncoder | `ACTIVE` | `RETRAINABLE` |
| LSTM | `ACTIVE` | `CONTRACT_GATED` |
| GNN | `ACTIVE_WITH_FALLBACK` | `CONTRACT_GATED` |
| FusionMLP | `ACTIVE` | `RETRAINABLE` |

## Per-Model Contribution Proof

The proof ran five real CIC/CSE rows through the exact Oracle Sensor path:

```python
from oracle_sensor.mutantshield_client import predict_decision
```

Each row recorded XGBoost, AutoEncoder, LSTM, GNN, fusion/final risk score, model consensus, confidence band, risk label, attack family, fallback flags, sequence context, graph context, and per-model latency.

Observed evidence:

- XGBoost produced class probabilities for every row.
- AutoEncoder produced reconstruction/anomaly scores for every row.
- LSTM produced attack probabilities for every row using the loaded LSTM model.
- GNN produced conservative fallback only on the first row with no graph history, then dynamic graph scores once history existed.
- FusionMLP produced the fused risk path; no weighted fusion fallback was used.

Detailed evidence is in:

- `reports/final/mutantshield_runtime_model_load_proof.json`
- `reports/final/mutantshield_runtime_model_contribution_proof.json`
- `reports/final/mutantshield_runtime_ensemble_proof.json`

## Oracle Core Preservation Proof

The proof sent one fused MutantShield output through:

```text
Dataset row -> MutantShield predict_decision() -> Oracle Core /oracle/process
```

Oracle Core returned HTTP `200` and preserved:

| Field | MutantShield | Oracle Core |
| --- | ---: | ---: |
| `risk_score` | `0.19486252175252103` | `0.19486252175252103` |
| `risk_label` | `BENIGN` | `BENIGN` |
| `model_consensus` | `1/4` | `1/4` |

Additional proof:

- `auth.verified`: `true`
- `audit.logged`: `true`
- `final_action`: `investigate`

Detailed evidence is in `reports/final/mutantshield_to_oracle_core_proof.json`.

## Existing Adaptation Retest

This retest used existing candidate artifacts only:

- CSE/HOIC repair candidate: `candidate-hoic-repair-20260623-194711-ac582d`
- DoHBrw native adapter: `candidate-dohbrw-adapter-20260623-221206-fc1dc5`

No training, threshold tuning, or promotion was performed.

| Dataset | Before Adaptation Accuracy | Before Recall | After Existing Candidate Accuracy | After Recall | Candidate |
| --- | ---: | ---: | ---: | ---: | --- |
| CIC-IDS2017 | `0.05` | `0.05` | `0.0` | `0.0` | HOIC repair candidate |
| CSE-CIC-IDS2018 | `0.25` | `0.0` | `1.0` | `1.0` | HOIC repair candidate |
| UNSW-NB15 | `0.3` | `0.066667` | `0.25` | `0.0` | HOIC repair candidate mapped path |
| DoHBrw | `0.0` | `0.0` | `0.8` | `0.8` | DoHBrw native adapter |
| Combined | `0.15` | `0.028571` | `0.5125` | `0.442857` | Existing candidates only |

Interpretation:

- The CSE repair candidate improves CSE rows strongly in this retest.
- The DoHBrw native adapter improves DoHBrw rows strongly in this retest.
- The HOIC repair candidate is not a universal replacement for CIC or UNSW.
- These are small proof samples (`20` rows per dataset), not a replacement for the larger repeated confidence evaluation.

Detailed evidence is in `reports/final/mutantshield_adaptation_retest_existing_artifacts.json`.

## Final Conclusion

LSTM and GNN are active during runtime detection. They are contract-gated for candidate retraining, not disabled in production inference. The verified runtime path uses XGBoost, AutoEncoder, LSTM, GNN, learned FusionMLP, and risk calibration, then Oracle Core receives and preserves the fused MutantShield decision.
