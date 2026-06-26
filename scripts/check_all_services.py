"""Verify all five ORACLE services are reachable before stress/baseline tests."""
from __future__ import annotations

import json
import sys

import requests

CHECKS = {
    "oracle_core": "http://127.0.0.1:8000/docs",
    "qauthcore": "http://127.0.0.1:8001/docs",
    "ethicq": "http://127.0.0.1:8002/docs",
    "chronoledger": "http://127.0.0.1:8003/health",
    "ghosttunnel": "http://127.0.0.1:8004/docs",
}


def check_all() -> dict[str, bool]:
    result = {}
    for name, url in CHECKS.items():
        try:
            r = requests.get(url, timeout=3)
            result[name] = r.status_code < 500
        except Exception:
            result[name] = False
    return result


def main() -> None:
    status = check_all()
    print(json.dumps(status, indent=2))
    missing = [k for k, ok in status.items() if not ok]
    if missing:
        print("\nNOT READY. Start missing services:")
        for name in missing:
            print(f"  - {name}")
        raise SystemExit(1)
    print("\nALL SERVICES READY")


if __name__ == "__main__":
    main()
