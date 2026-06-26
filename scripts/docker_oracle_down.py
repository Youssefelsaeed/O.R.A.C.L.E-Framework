"""Stop the Dockerized ORACLE runtime stack."""
from __future__ import annotations

from docker_oracle_common import docker_available, print_result, run_compose


def main() -> None:
    ok, message = docker_available()
    if not ok:
        print(message)
        raise SystemExit(1)
    print(message)
    result = run_compose(["down"], timeout=300)
    raise SystemExit(print_result(result))


if __name__ == "__main__":
    main()
