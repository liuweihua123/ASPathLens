#!/usr/bin/env python3
"""Download CAIDA AS2Org latest file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import AS2ORG_LATEST_URL, ASORG_RAW_DIR, TMP_DIR


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=AS2ORG_LATEST_URL)
    args = parser.parse_args()
    ASORG_RAW_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    name = "latest.as-org2info.txt.gz"
    if "202" in args.url:
        name = args.url.rstrip("/").split("/")[-1]
    tmp = TMP_DIR / name
    dest = ASORG_RAW_DIR / name
    print(f"Downloading {args.url} ...")
    r = requests.get(args.url, stream=True, timeout=600)
    r.raise_for_status()
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)
    if tmp.stat().st_size < 1000:
        raise SystemExit("Downloaded file too small; aborting.")
    tmp.replace(dest)
    print(f"Saved to {dest}")


if __name__ == "__main__":
    main()