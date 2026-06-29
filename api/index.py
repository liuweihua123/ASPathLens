"""Vercel Serverless Function entry point.

Wraps the FastAPI app from backend/app/main.py for Vercel deployment.
"""

import sys
from pathlib import Path

# Add backend directory to Python path
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.main import app  # noqa: E402,F401
