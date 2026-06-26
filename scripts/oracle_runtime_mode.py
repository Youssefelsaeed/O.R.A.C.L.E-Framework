"""Runtime mode helpers for operator-safe validation scripts."""
from __future__ import annotations

import argparse
import signal
import time
from typing import Any, Dict, List

from oracle_stack_common import check_health, kill_all_ports, start_services, wait_for_health


def add_runtime_mode_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manage-stack",
        action="store_true",
        help="Start ORACLE services for this test and stop only services started by this process.",
    )
    parser.add_argument(
        "--kill-existing",
        action="store_true",
        help="Only valid with --manage-stack. Kill existing ORACLE ports before starting managed services.",
    )


def existing_stack_ready() -> bool:
    status = check_health(timeout=3.0)
    return bool(status) and all(status.values())


def require_or_manage_stack(args: argparse.Namespace, *, max_wait_s: float = 120.0) -> tuple[bool, List[Any], Dict[str, bool]]:
    """Return (managed, procs, health) without stopping services we did not start."""
    if getattr(args, "manage_stack", False):
        if getattr(args, "kill_existing", False):
            kill_all_ports()
        procs = start_services()
        health = wait_for_health(max_wait_s=max_wait_s)
        return True, procs, health

    health = check_health(timeout=3.0)
    if not all(health.values()):
        missing = [name for name, ok in health.items() if not ok]
        raise RuntimeError(
            "existing_stack_not_ready:"
            + ",".join(missing)
            + " Start the stack with `python scripts/start_oracle_stack.py --gui --kill-existing` "
            + "or rerun with --manage-stack."
        )
    return False, [], health


def shutdown_owned_stack(procs: List[Any]) -> None:
    """Stop only processes created by this process."""
    for proc in procs:
        if proc.poll() is None:
            try:
                proc.send_signal(signal.SIGTERM)
            except Exception:
                proc.terminate()
    time.sleep(2)
    for proc in procs:
        if proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
