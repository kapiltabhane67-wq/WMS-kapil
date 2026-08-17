"""Catch-all Vercel Python function for every `/api/*` backend route.

Vercel's Python starter treats `api/index.py` as the API entrypoint, but in a
Next.js + Python mixed project some deployments can still let deep API paths
fall through to Next.js. This file makes `/api/v1/...`, `/api/docs`, and all
other API routes explicitly resolve to the same FastAPI app.
"""

from api.index import app
