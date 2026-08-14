# Folder Structure

```text
wms/
├── frontend/
│   └── Next.js + TypeScript + Tailwind
│
├── backend/
│   ├── main.py                         # Only starts the app
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini
│   ├── migrations/
│   ├── commons/                        # Shared helpers used by every module
│   │   ├── auth.py                     # Password hashing, sessions, role checks
│   │   ├── config.py                   # Settings and database path
│   │   ├── logger.py                   # App logger
│   │   └── exceptions.py               # Shared exception helpers
│   ├── core/
│   │   ├── apis/
│   │   │   ├── api.py                  # Builds FastAPI app, middleware, routers
│   │   │   ├── dependencies.py         # DB/session/current-user dependencies
│   │   │   └── routes/                 # Endpoint files by business area
│   │   │       ├── auth_router.py
│   │   │       ├── admin_router.py
│   │   │       ├── dashboard_router.py
│   │   │       ├── receiving_router.py
│   │   │       ├── inventory_router.py
│   │   │       ├── order_router.py
│   │   │       ├── fulfillment_router.py
│   │   │       └── document_router.py
│   │   ├── schemas/
│   │   │   ├── requests/
│   │   │   │   └── wms_request.py      # Input validation models
│   │   │   └── responses/
│   │   │       └── wms_response.py     # Output/response models
│   │   ├── controllers/
│   │   │   ├── auth_controller.py
│   │   │   ├── org_admin_controller.py
│   │   │   ├── warehouse_manager_controller.py
│   │   │   ├── receiver_controller.py
│   │   │   ├── picker_packer_controller.py
│   │   │   ├── seller_viewer_controller.py
│   │   │   ├── inventory_controller.py
│   │   │   ├── document_controller.py
│   │   │   └── user_controller.py      # User business logic: create, update, activate, reset password
│   │   ├── cruds/
│   │   │   ├── base.py                 # Generic SQLite DB helpers
│   │   │   └── user_crud.py            # User table/session/warehouse-access DB operations
│   │   ├── models/
│   │   │   └── user_model.py           # User roles, status enum, warehouse-role rules
│   │   ├── database/
│   │   │   ├── database.py             # Clean database import surface
│   │   │   ├── connection.py           # SQLite connection helpers
│   │   │   └── seed.py                 # Bootstrap admin and tables
│   │   ├── services/                   # WMS domain services
│   │   │   ├── setup_service.py        # Seller, warehouse, bin, product setup
│   │   │   ├── receiving_service.py    # Receiver stock intake flow
│   │   │   ├── inventory_service.py    # Inventory movement ledger
│   │   │   ├── orders_service.py       # Order import + reservation
│   │   │   ├── fulfillment_service.py  # Pick, pack, label, dispatch
│   │   │   ├── documents_service.py    # Receipts, invoices, labels
│   │   │   ├── manager_service.py      # Warehouse manager console
│   │   │   ├── admin_service.py        # Settings, audit, reports
│   │   │   └── views_service.py        # Filtered read-only views/reference data
│   │   ├── integrations/               # Marketplace/carrier integration adapters
│   │   ├── jobs/                       # Background jobs
│   │   └── utils/
│   │       └── email/
│   │           └── email_service.py    # Welcome-email builder
│   └── tests/
│
├── docker-compose.yml
├── scripts/
│   └── smoke_core_flow.py              # Automated role + end-to-end flow test
└── docs/
```

The tutorial example mentioned MongoDB in `database/database.py`; this WMS uses SQLite for the MVP, so `database.py` exposes our SQLite connection layer cleanly.
