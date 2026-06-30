"""Helpers for discovering the latest CAIDA dataset files."""

from __future__ import annotations

import re

import requests

from app.config import AS2ORG_DIR, ASREL_SERIAL2_DIR

ASREL_PATTERN = re.compile(r'(\d{8}\.as-rel2\.txt\.bz2)')
AS2ORG_PATTERN = re.compile(r'(\d{8}\.as-org2info\.txt\.gz)')


def _fetch_listing(url: str) -> str:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def _latest_match(pattern: re.Pattern[str], content: str) -> str:
    matches = sorted(set(pattern.findall(content)))
    if not matches:
        raise RuntimeError(f"No dataset filenames matched pattern {pattern.pattern!r}")
    return matches[-1]


def latest_asrel_url() -> str:
    listing = _fetch_listing(ASREL_SERIAL2_DIR)
    latest_name = _latest_match(ASREL_PATTERN, listing)
    return f"{ASREL_SERIAL2_DIR}{latest_name}"


def latest_as2org_url() -> str:
    listing = _fetch_listing(AS2ORG_DIR)
    latest_name = _latest_match(AS2ORG_PATTERN, listing)
    return f"{AS2ORG_DIR}{latest_name}"
