from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Iterable, Optional

import httpx


class OracleSender:
    """Rate-limited sender that posts flows to Oracle Core."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        *,
        max_requests_per_second: float = 10.0,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._period = 1.0 / max_requests_per_second if max_requests_per_second > 0 else 0
        self._timeout = httpx.Timeout(timeout_seconds)
        self._last_sent: float = 0.0

    async def _sleep_if_needed(self) -> None:
        if self._period <= 0:
            return
        now = time.time()
        elapsed = now - self._last_sent
        if elapsed < self._period:
            await asyncio.sleep(self._period - elapsed)
        self._last_sent = time.time()

    async def send_flow(self, client: httpx.AsyncClient, flow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a single flow to OracleCore; returns parsed JSON or None on error."""
        await self._sleep_if_needed()
        url = f"{self._base_url}/oracle/process"
        try:
            resp = await client.post(url, json=flow, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as exc:
            print(f"[oracle_sensor] send_flow request error: {exc!s}")
        except httpx.HTTPStatusError as exc:
            print(f"[oracle_sensor] send_flow HTTP {exc.response.status_code}: {exc.response.text[:200]}")
        return None

    async def run_loop(
        self,
        packet_source: Iterable[Dict[str, Any]],
    ) -> None:
        """
        Consume packet metadata dicts, build flows, and send to OracleCore.

        packet_source should be something like a generator that yields
        dicts with src_ip/dst_ip keys (see sniffer.start_sniffer).
        """
        from .flow_builder import build_flow

        async with httpx.AsyncClient() as client:
            for pkt in packet_source:
                flow = build_flow(pkt)
                await self.send_flow(client, flow)

