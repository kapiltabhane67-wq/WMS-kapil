# Whitfield WMS

Multi-seller warehouse management system for Whitfield Fulfillment.

This first build focuses on the core operational flow:

1. Seller or marketplace order arrives.
2. Order is created with duplicate protection.
3. Stock is reserved from the correct warehouse/bin.
4. Picker receives a task.
5. Item is scanned and picked.
6. Package is packed and invoice/label metadata is generated.
7. Shipment is dispatched.
8. Physical stock is deducted and tracking/status is updated.

The important rule is that inventory is not stored as one editable number. Every stock change goes through an inventory movement ledger and an audit log.

## Current Stack

- Backend: FastAPI + Pydantic
- Database: SQLite for local MVP, structured so it can move to PostgreSQL
- Frontend: Next.js + TypeScript + Tailwind
- Realtime/AI: planned next layer after the core flow is stable

See [folder-structure.md](docs/folder-structure.md) for the project structure.

## Run Backend

```powershell
cd "C:\Users\kapil\OneDrive\Documents\New project\whitfield-wms\backend"
python -m uvicorn main:app --reload --port 8016
```

Open:

- API health: `http://127.0.0.1:8016/health`
- API docs: `http://127.0.0.1:8016/docs`

On first startup, the app creates only the bootstrap admin. All sellers, warehouses, bins, products, and users are created from Setup.

## Setup Clean Client Database

```powershell
cd "C:\Users\kapil\OneDrive\Documents\New project\whitfield-wms"
python scripts\setup_client_database.py
```

Expected clean starting data:

```text
sellers: 0
warehouses: 0
bins: 0
products: 0
users: 1
sales_orders: 0
inventory_balances: 0
```

## Run Frontend

```powershell
cd "C:\Users\kapil\OneDrive\Documents\New project\whitfield-wms\frontend"
npm install
npm run dev
```

Open:

- App: `http://127.0.0.1:3001`

## Bootstrap Admin

On an empty database, the app creates only one bootstrap admin. Configure it with:

```text
BOOTSTRAP_ADMIN_EMAIL
BOOTSTRAP_ADMIN_NAME
BOOTSTRAP_ADMIN_PASSWORD
```

After logging in as bootstrap admin, use Setup to create real sellers, warehouses, bins, products, and users.

After login, the backend returns a bearer token. Normal API endpoints now require that token.

## Vercel Full Deployment

The project includes a Vercel serverless entrypoint:

```text
api/index.py
```

That file imports the existing FastAPI backend from `backend/core/apis/api.py` and mounts it under:

```text
/api
```

So after Vercel deployment:

- Frontend app: `https://your-vercel-domain.vercel.app`
- Backend health: `https://your-vercel-domain.vercel.app/api/health`
- Backend docs: `https://your-vercel-domain.vercel.app/api/docs`
- Auth login: `https://your-vercel-domain.vercel.app/api/v1/auth/login`

The frontend automatically uses `/api` in production, so no backend URL is needed when frontend and backend are deployed together on Vercel.

Important production note: Vercel serverless file storage is temporary. The current SQLite database can run there for a functional deployed demo, but long-term client data should be moved to a persistent database such as PostgreSQL on Neon, Supabase, or Railway.

## Smoke Test

After starting the backend, run:

```powershell
cd "C:\Users\kapil\OneDrive\Documents\New project\whitfield-wms"
python scripts\smoke_core_flow.py
```

The smoke test receives inventory, imports an order, reserves stock, picks, packs, dispatches, and verifies that stock is deducted only at dispatch.
