#!/usr/bin/env python3
"""Download CAIDA AS2Org latest file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import ASORG_RAW_DIR, TMP_DIR
from scripts.caida_release import latest_as2org_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="")
    args = parser.parse_args()
    url = args.url or latest_as2org_url()
    ASORG_RAW_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    name = url.rstrip("/").split("/")[-1]
    tmp = TMP_DIR / name
    dest = ASORG_RAW_DIR / name
    if dest.exists():
        print(f"Latest AS2Org already present: {dest.name}")
        return
    print(f"Downloading {url} ...")
    r = requests.get(url, stream=True, timeout=600)
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
