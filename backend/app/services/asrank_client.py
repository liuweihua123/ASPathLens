"""CAIDA ASRank API client with cache (enhancement only)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import requests

from app.config import (
    ASRANK_CACHE_TTL_DAYS,
    ASRANK_GRAPHQL_URL,
    ASRANK_REQUEST_TIMEOUT_SEC,
    CACHE_DIR,
)
from app.db.database import get_connection, init_db


def _cache_get(key: str) -> dict | None:
    try:
        init_db()
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            row = conn.execute(
                "SELECT response_json, expires_at FROM asrank_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if not row:
                return None
            if row["expires_at"] < now:
                return None
            return json.loads(row["response_json"])
    except Exception:
        return None


def _cache_set(key: str, data: dict) -> None:
    try:
        init_db()
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=ASRANK_CACHE_TTL_DAYS)
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO asrank_cache (cache_key, response_json, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                  response_json=excluded.response_json,
                  created_at=excluded.created_at,
                  expires_at=excluded.expires_at
                """,
                (key, json.dumps(data), now.isoformat(), expires.isoformat()),
            )
    except Exception:
        pass


def _graphql(query: str, variables: dict | None = None) -> dict | None:
    try:
        r = requests.post(
            ASRANK_GRAPHQL_URL,
            json={"query": query, "variables": variables or {}},
            timeout=ASRANK_REQUEST_TIMEOUT_SEC,
        )
        r.raise_for_status()
        body = r.json()
        if body.get("errors"):
            return None
        return body.get("data")
    except requests.RequestException:
        return None


def health_check() -> tuple[bool, str]:
    q = "{ asn(asn: \"15169\") { asn } }"
    data = _graphql(q)
    if data and data.get("asn"):
        return True, "ASRank API reachable"
    return False, "ASRank enhancement unavailable."


def asrank_health_check() -> tuple[bool, str]:
    return health_check()


def get_asn_profile(asn: str) -> dict:
    key = f"asn_profile:{asn}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    q = """
    query($asn: String!) {
      asn(asn: $asn) {
        asn organization { orgId orgName country iso }
        rank degree customerCone { numberAsns numberPrefixes }
      }
    }
    """
    data = _graphql(q, {"asn": asn})
    result = {"available": False, "asn": asn}
    if data and data.get("asn"):
        result = {"available": True, **data["asn"]}
    _cache_set(key, result)
    return result


def get_asn_links(asn: str) -> dict:
    key = f"asn_links:{asn}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    result = {"available": False, "asn": asn, "note": "Use local ASRelationship for core links."}
    _cache_set(key, result)
    return result


def get_organization(org_id: str) -> dict:
    key = f"org:{org_id}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    result = {"available": False, "org_id": org_id}
    _cache_set(key, result)
    return result