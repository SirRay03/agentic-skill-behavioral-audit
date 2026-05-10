#!/usr/bin/env python3
"""Parse a tcpdump pcap file to extract DNS queries (hostnames) and TCP-SYN destinations.

Uses scapy. Install with: pip install scapy

Usage:
    parse-pcap.py path/to/net.pcap
"""
import sys
import json
from collections import defaultdict
from pathlib import Path

try:
    from scapy.all import rdpcap, DNS, TCP, IP, IPv6
except ImportError:
    print("ERROR: scapy not installed. Run: pip install scapy", file=sys.stderr)
    sys.exit(1)


def parse(pcap_path: Path) -> dict:
    dns_queries: set[str] = set()
    tcp_counts: dict[tuple[str, int], int] = defaultdict(int)

    pkts = rdpcap(str(pcap_path))
    for pkt in pkts:
        # DNS queries
        if pkt.haslayer(DNS) and pkt[DNS].qd is not None:
            try:
                qname = pkt[DNS].qd.qname
                if isinstance(qname, bytes):
                    qname = qname.decode("utf-8", errors="replace")
                qname = qname.rstrip(".")
                if qname:
                    dns_queries.add(qname)
            except Exception:
                pass
        # TCP SYN packets — initiating connections (SYN flag set, ACK clear)
        if pkt.haslayer(TCP):
            flags = int(pkt[TCP].flags)
            if (flags & 0x02) and not (flags & 0x10):  # SYN, not SYN-ACK
                if pkt.haslayer(IP):
                    dst = pkt[IP].dst
                elif pkt.haslayer(IPv6):
                    dst = pkt[IPv6].dst
                else:
                    continue
                tcp_counts[(dst, int(pkt[TCP].dport))] += 1

    return {
        "dns_queries": sorted(dns_queries),
        "tcp_destinations": [
            {"ip": ip, "port": port, "count": count}
            for (ip, port), count in sorted(tcp_counts.items())
        ],
        "summary": {
            "n_dns_queries": len(dns_queries),
            "n_tcp_destinations": len(tcp_counts),
            "total_packets": len(pkts),
        },
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: parse-pcap.py <net.pcap>", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(parse(Path(sys.argv[1])), indent=2))
