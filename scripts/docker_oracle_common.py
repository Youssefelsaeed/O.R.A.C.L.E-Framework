"""Shared Docker Compose helpers for ORACLE runtime scripts."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Sequence

ROOT = Path(__file__).resolve().parents[1]
DOCKER_UNAVAILABLE = "Docker Desktop/Linux engine is not available."


def run_compose(args: Sequence[str], *, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def docker_available() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["docker", "info"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError:
        return False, DOCKER_UNAVAILABLE
    except Exception as exc:
        return False, f"{DOCKER_UNAVAILABLE} ({exc})"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return False, f"{DOCKER_UNAVAILABLE} {detail}".strip()
    return True, "Docker engine available."


def print_result(result: subprocess.CompletedProcess[str]) -> int:
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode


def service_names() -> List[str]:
    return ["oracle-core", "qauthcore", "ethicq", "chronoledger", "ghosttunnel", "oracle-gui"]
