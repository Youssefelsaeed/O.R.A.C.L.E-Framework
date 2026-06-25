from __future__ import annotations

"""
ORACLE SENSOR entrypoint.

This script ties together:
  - packet sniffer (Scapy)
  - flow builder
  - OracleCore sender

It is written so it can also be unit-tested by substituting the sniffer
with a synthetic packet iterator.
"""

import asyncio
from collections import deque
from typing import Deque, Dict

from .sender import OracleSender
from .sniffer import start_sniffer


def _packet_queue_source(queue: Deque[Dict[str, object]]):
    """Simple iterator that yields from a shared packet queue."""
    while True:
        if not queue:
            continue
        pkt = queue.popleft()
        yield pkt


async def main() -> None:
    queue: Deque[Dict[str, object]] = deque()

    def _handle_packet(meta: Dict[str, object]) -> None:
        queue.append(meta)

    # Start sniffer in a background thread (blocking call inside).
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, start_sniffer, _handle_packet)

    sender = OracleSender(base_url="http://localhost:8000", max_requests_per_second=10.0)
    await sender.run_loop(_packet_queue_source(queue))


if __name__ == "__main__":
    asyncio.run(main())

