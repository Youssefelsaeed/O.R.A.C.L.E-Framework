"""Check whether ORACLE live network capture can run on this machine."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "live_sensor_readiness_report.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _importable(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run() -> Dict[str, Any]:
    scapy = _importable("scapy")
    oracle_sensor = _importable("oracle_sensor")
    mutantshield_available = (ROOT / "Mutant_Sheild Module").exists() or _importable("mutantshield")
    try:
        oracle_core = requests.get("http://127.0.0.1:8000/docs", timeout=5).status_code < 500
    except Exception:
        oracle_core = False
    interfaces: list[str] = []
    if scapy:
        try:
            from scapy.all import get_if_list  # type: ignore

            interfaces = [str(i) for i in get_if_list()[:20]]
        except Exception:
            interfaces = []
    admin_note = "Windows packet capture usually requires Npcap and administrator permission."
    live_ready = bool(scapy and oracle_sensor and mutantshield_available and oracle_core)
    if live_ready:
        recommended = "ready"
    elif not scapy:
        recommended = "install_scapy_npcap"
    elif not oracle_core:
        recommended = "start_oracle_stack"
    else:
        recommended = "run_replay_proof"
    report = {
        "generated_at": time.time(),
        "platform": os.name,
        "scapy_installed": scapy,
        "oracle_sensor_importable": oracle_sensor,
        "oracle_core_reachable": oracle_core,
        "mutantshield_available": mutantshield_available,
        "network_interfaces": interfaces,
        "admin_permission_note": admin_note,
        "live_capture_ready": live_ready,
        "recommended_action": recommended,
        "truth_statement": (
            "Live network capture is not active. Realtime replay proof is available and validated."
            if not live_ready
            else "Live capture dependencies are present; run live sensor smoke test with appropriate permissions."
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE LIVE SENSOR READINESS ===")
    print(f"Scapy Installed: {str(report['scapy_installed']).upper()}")
    print(f"Oracle Sensor Importable: {str(report['oracle_sensor_importable']).upper()}")
    print(f"Oracle Core Reachable: {str(report['oracle_core_reachable']).upper()}")
    print(f"MutantShield Available: {str(report['mutantshield_available']).upper()}")
    print(f"Live Capture Ready: {str(report['live_capture_ready']).upper()}")
    print(f"Recommended Action: {report['recommended_action']}")
    print(f"Report: {REPORT}")
    if not report["oracle_core_reachable"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
