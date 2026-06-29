"""Load CAIDA AS Relationship serial-2 files into memory or SQLite."""

from __future__ import annotations

import bz2
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

RelType = Literal["p2c", "c2p", "p2p", "unknown"]


@dataclass
class AsRelParseStats:
    edge_count: int = 0
    p2c_count: int = 0
    c2p_count: int = 0
    p2p_count: int = 0
    unique_asn_count: int = 0
    dataset_date: str = ""
    file_name: str = ""
    parse_time: str = ""


@dataclass
class AsRelStore:
    relationship_map: dict[tuple[str, str], str] = field(default_factory=dict)
    stats: AsRelParseStats = field(default_factory=AsRelParseStats)
    version: str = ""

    def get_relationship(self, asn_a: str, asn_b: str) -> str:
        return self.relationship_map.get((asn_a, asn_b), "unknown")


def _parse_line(line: str) -> tuple[str, str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split("|")
    if len(parts) < 3:
        return None
    a, b, rel_flag = parts[0].strip(), parts[1].strip(), parts[2].strip()
    if not a.isdigit() or not b.isdigit():
        return None
    a, b = str(int(a)), str(int(b))
    if rel_flag == "-1":
        return (a, b, "p2c")
    if rel_flag == "0":
        return (a, b, "p2p")
    return None


def parse_asrel_file(path: Path, version: str | None = None) -> AsRelStore:
    store = AsRelStore()
    store.stats.file_name = path.name
    store.stats.parse_time = datetime.now(timezone.utc).isoformat()
    m = re.search(r"(\d{8})", path.name)
    store.stats.dataset_date = m.group(1) if m else ""
    store.version = version or store.stats.dataset_date or path.stem

    asns: set[str] = set()
    open_fn = bz2.open if path.suffix == ".bz2" or path.name.endswith(".bz2") else open
    mode = "rt" if path.suffix == ".bz2" or path.name.endswith(".bz2") else "r"

    with open_fn(path, mode, encoding="utf-8", errors="replace") as f:
        for line in f:
            parsed = _parse_line(line)
            if not parsed:
                continue
            a, b, rel_ab = parsed
            asns.add(a)
            asns.add(b)
            if rel_ab == "p2c":
                store.relationship_map[(a, b)] = "p2c"
                store.relationship_map[(b, a)] = "c2p"
                store.stats.p2c_count += 1
                store.stats.c2p_count += 1
            elif rel_ab == "p2p":
                store.relationship_map[(a, b)] = "p2p"
                store.relationship_map[(b, a)] = "p2p"
                store.stats.p2p_count += 2

    store.stats.edge_count = len(store.relationship_map)
    store.stats.unique_asn_count = len(asns)
    return store


def load_asrel_from_path(path: str | Path) -> AsRelStore:
    return parse_asrel_file(Path(path))