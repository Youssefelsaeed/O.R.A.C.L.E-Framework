"""Show recent Docker Compose logs for ORACLE runtime services."""
from __future__ import annotations

import argparse

from docker_oracle_common import docker_available, print_result, run_compose


def main() -> None:
    parser = argparse.ArgumentParser(description="Show ORACLE Docker logs")
    parser.add_argument("--tail", default="100")
    parser.add_argument("service", nargs="?")
    args = parser.parse_args()
    ok, message = docker_available()
    if not ok:
        print(message)
        raise SystemExit(1)
    print(message)
    cmd = ["logs", f"--tail={args.tail}"]
    if args.service:
        cmd.append(args.service)
    result = run_compose(cmd, timeout=300)
    raise SystemExit(print_result(result))


if __name__ == "__main__":
    main()
