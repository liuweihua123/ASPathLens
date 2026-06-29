#!/usr/bin/env python3
"""Download and parse CAIDA datasets (safe: tmp first, validate before activate)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SCRIPTS = BACKEND / "scripts"


def run(name: str) -> None:
    print(f"\n=== {name} ===")
    subprocess.check_call([sys.executable, str(SCRIPTS / name)])


def main():
    steps = [
        "download_asrel.py",
        "download_as2org.py",
        "parse_asrel.py",
        "parse_as2org.py",
    ]
    for s in steps:
        try:
            run(s)
        except subprocess.CalledProcessError as e:
            print(f"Step failed: {s} (exit {e.returncode}). Active data unchanged.")
            sys.exit(1)
    print("\nUpdate complete.")


if __name__ == "__main__":
    main()