#!/usr/bin/env python3
"""Download CAIDA AS Relationship serial-2 file to data/raw/as_relationship/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import ASREL_LATEST_EXAMPLE, ASREL_RAW_DIR, TMP_DIR


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=ASREL_LATEST_EXAMPLE)
    args = parser.parse_args()
    ASREL_RAW_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    name = args.url.rstrip("/").split("/")[-1]
    tmp = TMP_DIR / name
    dest = ASREL_RAW_DIR / name
    print(f"Downloading {args.url} ...")
    r = requests.get(args.url, stream=True, timeout=600)
    r.raise_for_status()
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)
    if tmp.stat().st_size < 1000:
        raise SystemExit("Downloaded file too small; aborting without overwrite.")
    tmp.replace(dest)
    print(f"Saved to {dest}")


if __name__ == "__main__":
    main()