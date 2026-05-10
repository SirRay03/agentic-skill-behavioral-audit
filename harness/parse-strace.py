#!/usr/bin/env python3
"""Parse a strace `-f -e trace=openat,open,creat,write,unlink,unlinkat,rename,renameat,connect`
log into a structured JSON of paths read/written/deleted and connect destinations.

Filtering rules:
- An open with O_WRONLY / O_RDWR / O_CREAT / O_APPEND / O_TRUNC is a write.
- All other opens are reads.
- Failed opens (return value < 0 with ENOENT etc.) are still recorded — they show
  the agent's intent, which is part of the capability footprint.

Usage:
    parse-strace.py path/to/syscalls.log
"""
import sys
import re
import json
from pathlib import Path

OPEN_RE = re.compile(
    r"""(?:openat|open|creat)\(
        (?:[^,]+,\s*)?         # optional dirfd arg
        "([^"]+)"              # path (group 1)
        (?:,\s*([A-Z_|]+))?    # flags (group 2, optional for creat)
    """,
    re.VERBOSE,
)

UNLINK_RE = re.compile(r"""(?:unlink|unlinkat)\([^"]*"([^"]+)" """, re.VERBOSE)
RENAME_RE = re.compile(r"""(?:rename|renameat)\([^"]*"([^"]+)"[^"]*"([^"]+)" """, re.VERBOSE)
CONNECT_INET_RE = re.compile(
    r"""connect\(\d+,\s*\{
        sa_family=AF_INET6?,\s*
        sin6?_port=htons\((\d+)\),\s*    # port (group 1)
        (?:sin6?_flowinfo=[^,]+,\s*)?
        (?:inet_addr|inet_pton|inet_pton\(AF_INET6,)\s*"([^"]+)"   # ip (group 2)
    """,
    re.VERBOSE,
)
# Simpler fallback for connect — just look for an IP address in any form
CONNECT_FALLBACK_RE = re.compile(
    r"""connect\(\d+,.*?(?:sin_port=htons\((\d+)\)|sin6_port=htons\((\d+)\)).*?(?:inet_addr|inet_pton)\(.*?"([0-9a-fA-F:.]+)" """,
    re.VERBOSE,
)


def write_flags(flags: str) -> bool:
    if not flags:
        return False  # creat() has no flags but always writes — handled below
    return any(f in flags for f in ("O_WRONLY", "O_RDWR", "O_CREAT", "O_APPEND", "O_TRUNC"))


def parse(log_path: Path) -> dict:
    paths_read: set[str] = set()
    paths_written: set[str] = set()
    paths_deleted: set[str] = set()
    connects: dict[tuple[str, int], int] = {}

    with log_path.open(errors="replace") as f:
        for line in f:
            # creat() always writes
            if "creat(" in line and "create(" not in line:
                m = re.search(r'creat\("([^"]+)"', line)
                if m:
                    paths_written.add(m.group(1))
                    continue
            # open / openat
            m = OPEN_RE.search(line)
            if m:
                path, flags = m.group(1), (m.group(2) or "")
                if write_flags(flags):
                    paths_written.add(path)
                else:
                    paths_read.add(path)
                continue
            # unlink
            m = UNLINK_RE.search(line)
            if m:
                paths_deleted.add(m.group(1))
                continue
            # rename
            m = RENAME_RE.search(line)
            if m:
                paths_deleted.add(m.group(1))
                paths_written.add(m.group(2))
                continue
            # connect
            m = CONNECT_INET_RE.search(line) or CONNECT_FALLBACK_RE.search(line)
            if m:
                groups = [g for g in m.groups() if g]
                # Disambiguate: ports are short numeric, ips contain . or :
                port = next((int(g) for g in groups if g.isdigit()), None)
                ip = next((g for g in groups if not g.isdigit()), None)
                if port and ip:
                    key = (ip, port)
                    connects[key] = connects.get(key, 0) + 1

    return {
        "paths_read": sorted(paths_read),
        "paths_written": sorted(paths_written),
        "paths_deleted": sorted(paths_deleted),
        "connects": [
            {"ip": ip, "port": port, "count": count}
            for (ip, port), count in sorted(connects.items())
        ],
        "summary": {
            "n_paths_read": len(paths_read),
            "n_paths_written": len(paths_written),
            "n_paths_deleted": len(paths_deleted),
            "n_connect_destinations": len(connects),
        },
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: parse-strace.py <syscalls.log>", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(parse(Path(sys.argv[1])), indent=2))
