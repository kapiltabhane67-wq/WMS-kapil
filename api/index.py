"""Vercel serverless entrypoint for the Whitfield WMS FastAPI backend.

This file is intentionally thin. It does not duplicate business logic.
It only makes the existing backend app importable from Vercel's required
`api/index.py` location and exposes the same FastAPI application under `/api`.
"""

from pathlib import Path
import sys

from fastapi import FastAPI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core.apis.api import app as backend_app  # noqa: E402


app = FastAPI(
    title="Whitfield WMS Serverless Gateway",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/api/health")
def serverless_health():
    return {
        "status": "ok",
        "service": "Whitfield WMS",
        "runtime": "vercel-serverless",
    }


app.mount("/api", backend_app)
app.mount("/", backend_app)
