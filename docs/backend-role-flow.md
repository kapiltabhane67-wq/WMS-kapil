# Backend Role Flow

This project follows the FastAPI production structure from the Day 2 notes:

```text
main.py
-> core/apis/api.py
-> core/apis/routes/*_router.py
-> core/controllers/*_controller.py
-> core/services/*
-> core/cruds/*
-> core/database/*
```

`main.py` only starts the app. `api.py` builds FastAPI, middleware, health check, and routers.

## Role-wise controller files

| Role / flow | Main controller file | Responsibility |
|---|---|---|
| Authentication | `backend/core/controllers/auth_controller.py` | login, logout, current user, reference data, change password |
| ORG_ADMIN | `backend/core/controllers/org_admin_controller.py` | sellers, warehouses, bins, products, users, settings, reports, audit |
| WAREHOUSE_MANAGER | `backend/core/controllers/warehouse_manager_controller.py` | dashboard, manager console, order import, order review, inventory adjustment |
| RECEIVER | `backend/core/controllers/receiver_controller.py` | complete receipt, receiving history |
| PICKER_PACKER | `backend/core/controllers/picker_packer_controller.py` | pick task list, scan item, pack order, dispatch shipment |
| SELLER_VIEWER | `backend/core/controllers/seller_viewer_controller.py` | read-only seller stock, orders, tracking, documents, movement history |
| Inventory | `backend/core/controllers/inventory_controller.py` | inventory rows, movement ledger, adjustment entry point |
| Documents | `backend/core/controllers/document_controller.py` | role-filtered documents and validated upload |
| Users | `backend/core/controllers/user_controller.py` | create/update/deactivate/reset user business rules |

## Example request journey

```text
Picker scans item
-> POST /v1/fulfillment/pick-tasks/{task_id}/scan
-> fulfillment_router.py
-> picker_packer_controller.py
-> fulfillment_service.py
-> inventory ledger / SQLite
```

## Core warehouse flow

```text
Marketplace order
-> order_router.py
-> warehouse_manager_controller.py
-> orders_service.py
-> stock reserved
-> pick task created
-> picker_packer_controller.py
-> fulfillment_service.py
-> invoice/label generated
-> shipment dispatched
-> physical stock deducted
```

## Why this is not one-file backend

The tutorial first shows a one-file auth API to teach the pain. This project uses the production version:

- request schemas live in `core/schemas/requests/`;
- response schemas live in `core/schemas/responses/`;
- route files are HTTP-only;
- controller files show role/business flow;
- service files contain domain logic;
- CRUD files contain reusable database operations;
- models contain enums and DB concepts;
- database files own SQLite setup and migrations.

