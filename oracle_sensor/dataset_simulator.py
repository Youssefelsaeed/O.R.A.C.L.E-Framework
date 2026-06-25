from __future__ import annotations

import argparse
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
import math

import httpx
import pandas as pd

from mutantshield.evolution.feature_mapping import map_cse_row_to_production_features

from .mutantshield_client import predict_decision


logger = logging.getLogger("oracle_sensor.dataset_simulator")

DEFAULT_CIC_DIR = Path(
    r"D:\MY STUDIES\UNIVERSITY\GRAD\Grad work\Modules\Mutant_Sheild Module\mutantshield\src\FinalVersion\Data set\CIC-2017 (baseline)"
)


CLIP_MIN = -1e6
CLIP_MAX = 1e6


def _sanitize_numeric_feature(feature: str, value: float) -> float:
    original = value
    if math.isnan(value):
        new_value = 0.0
    elif math.isinf(value):
        new_value = CLIP_MAX if value > 0 else CLIP_MIN
    else:
        new_value = min(max(value, CLIP_MIN), CLIP_MAX)

    if new_value != original:
        logger.info(
            {
                "msg": "feature_sanitized",
                "feature": feature,
                "original_value": original,
                "new_value": new_value,
            }
        )
    return float(new_value)


def _detect_label_column(df: pd.DataFrame) -> Optional[str]:
    for candidate in ("Label", " Label", "label"):
        if candidate in df.columns:
            return candidate
    return None


def _normalize_label(value: Any) -> str:
    v = str(value).strip()
    if v.upper() == "BENIGN":
        return "BENIGN"
    return v if v else "UNKNOWN"


def _pick_src_dst(row: pd.Series, idx: int) -> tuple[str, str]:
    src = row.get("Source IP", row.get("src_ip", f"192.168.{idx // 256}.{idx % 256}"))
    dst = row.get("Destination IP", row.get("dst_ip", f"10.0.{idx // 256}.{idx % 256}"))
    return str(src), str(dst)


def _row_to_mutantshield_features(row: pd.Series) -> Dict[str, float]:
    """
    Convert CIC row to numeric feature dict expected by MutantShield pipeline.

    Non-numeric and metadata columns are skipped.
    """
    mapped, quality = map_cse_row_to_production_features(row)
    if mapped and quality.get("mapped_count", 0) > 0:
        return mapped

    features: Dict[str, float] = {}
    for col, val in row.items():
        col_name = str(col).strip()
        if col_name.lower() in {"label", "source ip", "destination ip", "flow_id", "id"}:
            continue
        try:
            f = float(val)
            f = _sanitize_numeric_feature(col_name, f)
            features[col_name] = f
        except Exception:
            continue
    return features


def _iter_rows(df: pd.DataFrame, mode: str, limit: int, seed: int) -> Iterable[tuple[int, pd.Series]]:
    if mode == "random":
        n = min(limit, len(df))
        sampled = df.sample(n=n, random_state=seed)
        for idx, row in sampled.iterrows():
            yield int(idx), row
    else:
        for i, (idx, row) in enumerate(df.iterrows()):
            if i >= limit:
                break
            yield int(idx), row


async def run_simulation(
    csv_path: Path,
    *,
    oracle_url: str = "http://localhost:8000",
    mode: str = "sequential",
    limit: int = 100,
    delay_ms: int = 50,
    seed: int = 42,
) -> Dict[str, int]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CIC CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    label_col = _detect_label_column(df)

    summary = {
        "total": 0,
        "benign_block": 0,
        "benign_investigate": 0,
        "attack_allow": 0,
    }

    oracle_endpoint = f"{oracle_url.rstrip('/')}/oracle/process"

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        for idx, row in _iter_rows(df, mode=mode, limit=limit, seed=seed):
            features = _row_to_mutantshield_features(row)
            decision_obj, _raw = predict_decision(features)

            src_ip, dst_ip = _pick_src_dst(row, idx)
            dataset_label = _normalize_label(row.get(label_col, "UNKNOWN") if label_col else "UNKNOWN")

            flow = {
                "flow_id": str(uuid.uuid4()),
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "risk_score": float(decision_obj.get("risk_score", 0.0)),
                "risk_label": str(decision_obj.get("risk_label", "LOW")),
                "is_attack": bool(decision_obj.get("is_attack", False)),
                "attack_family": str(decision_obj.get("attack_family", dataset_label)),
                "confidence_band": str(decision_obj.get("confidence_band", "LOW")),
                "model_consensus": str(decision_obj.get("model_consensus", "0/0")),
            }

            final_action = "send_failed"
            try:
                resp = await client.post(oracle_endpoint, json=flow)
                if resp.status_code == 200:
                    body = resp.json()
                    final_action = str((body.get("action") or {}).get("final_action", "unknown"))
                else:
                    final_action = f"http_{resp.status_code}"
            except Exception as exc:
                logger.error({"msg": "oracle_send_error", "error": str(exc), "flow_id": flow["flow_id"]})

            logger.info(
                {
                    "dataset_label": dataset_label,
                    "predicted_score": flow["risk_score"],
                    "predicted_label": flow["risk_label"],
                    "final_action": final_action,
                }
            )

            # mismatch tracking
            is_benign = dataset_label.upper() == "BENIGN"
            if is_benign and final_action == "block":
                summary["benign_block"] += 1
            if is_benign and final_action == "investigate":
                summary["benign_investigate"] += 1
            if (not is_benign) and final_action == "allow":
                summary["attack_allow"] += 1

            summary["total"] += 1
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)

    logger.info({"summary": summary})
    return summary


def _pick_default_csv() -> Path:
    if not DEFAULT_CIC_DIR.exists():
        raise FileNotFoundError(f"CIC directory not found: {DEFAULT_CIC_DIR}")
    csv_files = sorted(DEFAULT_CIC_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files in {DEFAULT_CIC_DIR}")
    return csv_files[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="ORACLE SENSOR CIC dataset simulator")
    parser.add_argument("--csv", type=str, default="", help="Path to CIC CSV file")
    parser.add_argument("--mode", choices=["sequential", "random"], default="sequential")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--delay-ms", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--oracle-url", type=str, default="http://localhost:8000")
    parser.add_argument("--log-level", type=str, default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    csv_path = Path(args.csv) if args.csv else _pick_default_csv()
    summary = asyncio.run(
        run_simulation(
            csv_path,
            oracle_url=args.oracle_url,
            mode=args.mode,
            limit=args.limit,
            delay_ms=args.delay_ms,
            seed=args.seed,
        )
    )
    print(summary)


if __name__ == "__main__":
    main()

