"""Load CAIDA AS2Org as-org2info files."""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class As2OrgParseStats:
    asn_count: int = 0
    org_count: int = 0
    country_count: int = 0
    dataset_date: str = ""
    file_name: str = ""
    parse_time: str = ""


@dataclass
class AsnOrgInfo:
    asn: str
    as_name: str = ""
    org_id: str = ""
    org_name: str = ""
    country: str = ""


@dataclass
class As2OrgStore:
    asn_to_org: dict[str, AsnOrgInfo] = field(default_factory=dict)
    org_to_asns: dict[str, list[str]] = field(default_factory=dict)
    org_meta: dict[str, dict] = field(default_factory=dict)
    stats: As2OrgParseStats = field(default_factory=As2OrgParseStats)
    version: str = ""

    def same_org(self, asn_a: str, asn_b: str) -> bool:
        oa = self.asn_to_org.get(asn_a)
        ob = self.asn_to_org.get(asn_b)
        if not oa or not ob or not oa.org_id or not ob.org_id:
            return False
        return oa.org_id == ob.org_id


def parse_as2org_file(path: Path, version: str | None = None) -> As2OrgStore:
    store = As2OrgStore()
    store.stats.file_name = path.name
    store.stats.parse_time = datetime.now(timezone.utc).isoformat()
    m = re.search(r"(\d{8})", path.name)
    store.stats.dataset_date = m.group(1) if m else ""
    store.version = version or store.stats.dataset_date or "latest"

    aut_records: dict[str, dict] = {}
    org_records: dict[str, dict] = {}

    open_fn = gzip.open if path.suffix == ".gz" or path.name.endswith(".gz") else open
    mode = "rt" if path.suffix == ".gz" or path.name.endswith(".gz") else "r"

    with open_fn(path, mode, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 4:
                continue
            if parts[0].isdigit():
                # aut|changed|aut_name|org_id|...
                asn = str(int(parts[0]))
                aut_records[asn] = {
                    "as_name": parts[2] if len(parts) > 2 else "",
                    "org_id": parts[3] if len(parts) > 3 else "",
                }
            else:
                org_id = parts[0]
                org_records[org_id] = {
                    "org_name": parts[2] if len(parts) > 2 else "",
                    "country": parts[3] if len(parts) > 3 else "",
                    "source": parts[4] if len(parts) > 4 else "",
                }

    countries: set[str] = set()
    for asn, rec in aut_records.items():
        org_id = rec.get("org_id", "")
        om = org_records.get(org_id, {})
        org_name = om.get("org_name", "")
        country = om.get("country", "")
        if country:
            countries.add(country)
        info = AsnOrgInfo(
            asn=asn,
            as_name=rec.get("as_name", ""),
            org_id=org_id,
            org_name=org_name,
            country=country,
        )
        store.asn_to_org[asn] = info
        store.org_to_asns.setdefault(org_id, []).append(asn)
        store.org_meta[org_id] = {
            "org_name": org_name,
            "country": country,
            "source": om.get("source", ""),
        }

    store.stats.asn_count = len(store.asn_to_org)
    store.stats.org_count = len(store.org_to_asns)
    store.stats.country_count = len(countries)
    return store


def load_as2org_from_path(path: str | Path) -> As2OrgStore:
    return parse_as2org_file(Path(path))