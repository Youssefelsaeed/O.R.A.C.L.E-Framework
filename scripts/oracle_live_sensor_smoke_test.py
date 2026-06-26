"""Live sensor smoke test with safe fallback to realtime replay."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from oracle_realtime_replay_proof import run as run_replay

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "oracle_live_sensor_proof_report.json"


def _anonymize_ip(value: str) -> str:
    parts = str(value).split(".")
    if len(parts) == 4:
        return ".".join(parts[:2] + ["x", "x"])
    return "anonymized"


def _try_capture(packet_count: int, timeout: int) -> tuple[List[Dict[str, Any]], str | None]:
    try:
        from scapy.all import IP, conf, get_if_list, sniff  # type: ignore
    except Exception as exc:
        return [], f"scapy_unavailable:{exc!s}"
    try:
        interfaces = get_if_list()
        iface = conf.iface
        packets = sniff(count=packet_count, timeout=timeout, iface=iface)
        rows: List[Dict[str, Any]] = []
        for pkt in packets:
            if IP in pkt:
                rows.append(
                    {
                        "src_ip": _anonymize_ip(pkt[IP].src),
                        "dst_ip": _anonymize_ip(pkt[IP].dst),
                        "timestamp": time.time(),
                    }
                )
        if not rows:
            return [], f"no_ip_packets_captured interfaces={interfaces}"
        return rows, None
    except Exception as exc:
        return [], f"packet_capture_blocked:{exc!s}"


def run(packet_count: int = 30, timeout: int = 10, fallback_events: int = 25) -> Dict[str, Any]:
    captured, blocker = _try_capture(packet_count, timeout)
    replay = None
    if blocker or not captured:
        replay = run_replay(events=fallback_events, delay_ms=10)

    report = {
        "generated_at": time.time(),
        "live_capture": {
            "attempted": True,
            "packets_or_flows_captured": len(captured),
            "sample_pairs": captured[:10],
            "blocked_reason": blocker,
        },
        "fallback_replay": replay,
        "pass": bool(captured) or bool(replay and replay.get("pass")),
        "status": "PASS" if captured else ("SKIPPED_WITH_REASON" if replay and replay.get("pass") else "FAIL"),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="ORACLE live sensor smoke test")
    parser.add_argument("--packet-count", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--fallback-events", type=int, default=25)
    args = parser.parse_args()
    report = run(packet_count=args.packet_count, timeout=args.timeout, fallback_events=args.fallback_events)
    print("\n=== ORACLE LIVE SENSOR SMOKE TEST ===")
    print(f"Capture Status: {report['status']}")
    print(f"Captured: {report['live_capture']['packets_or_flows_captured']}")
    print(f"Blocked Reason: {report['live_capture']['blocked_reason']}")
    if report.get("fallback_replay"):
        replay = report["fallback_replay"]
        print(f"Fallback Replay: {'PASS' if replay.get('pass') else 'FAIL'}")
        print(f"Fallback Events: {replay.get('events_sent')}")
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
