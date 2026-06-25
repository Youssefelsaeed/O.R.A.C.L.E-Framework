from __future__ import annotations

"""
ORACLE SENSOR packet sniffer.

This module is responsible ONLY for capturing basic IP metadata from live
traffic. It is intentionally thin so it can be swapped or mocked in tests.

Scapy is used when available; if it is not installed or the process does not
have sufficient privileges, the sniffer will raise a clear RuntimeError.
"""

from typing import Callable, Optional


def _load_scapy():
    try:
        # Import lazily so unit tests can run without scapy installed.
        from scapy.all import IP, sniff  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Scapy is required to run ORACLE SENSOR sniffer but is not installed "
            "or failed to import. Install with `pip install scapy` and run with "
            "appropriate privileges."
        ) from exc
    return IP, sniff


def start_sniffer(
    packet_handler: Callable[[dict], None],
    *,
    interface: Optional[str] = None,
    bpf_filter: str = "ip",
) -> None:
    """
    Start a blocking packet sniffer.

    For each captured packet with an IP header, `packet_handler` is called with:

        {
          "src_ip": str,
          "dst_ip": str,
          "protocol": int,
          "length": int,
        }
    """
    IP, sniff = _load_scapy()

    def _on_packet(pkt) -> None:
        if IP not in pkt:
            return
        ip = pkt[IP]
        meta = {
            "src_ip": ip.src,
            "dst_ip": ip.dst,
            "protocol": int(ip.proto),
            "length": int(len(pkt)),
        }
        packet_handler(meta)

    sniff(
        iface=interface,
        filter=bpf_filter,
        prn=_on_packet,
        store=False,
    )

