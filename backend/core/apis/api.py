from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.apis.routes import (
    admin_router,
    auth_router,
    chat_router,
    dashboard_router,
    document_router,
    fulfillment_router,
    inventory_router,
    order_router,
    receiving_router,
)
from core.database.connection import db_connection, init_db
from core.database.seed import seed_if_empty
from commons.config import settings


app = FastAPI(title="Whitfield WMS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    with db_connection() as conn:
        seed_if_empty(conn)


@app.get("/health")
def health():
    return {"status": "ok", "service": "Whitfield WMS"}


app.include_router(auth_router.router, tags=["Authentication and Session"])
app.include_router(admin_router.router, tags=["ORG_ADMIN Setup and Governance"])
app.include_router(dashboard_router.router, tags=["Dashboard and Warehouse Manager"])
app.include_router(receiving_router.router, tags=["RECEIVER Flow"])
app.include_router(inventory_router.router, tags=["Inventory Ledger"])
app.include_router(order_router.router, tags=["Order and Marketplace Flow"])
app.include_router(fulfillment_router.router, tags=["PICKER_PACKER Fulfillment Flow"])
app.include_router(document_router.router, tags=["Documents and File Upload"])
app.include_router(chat_router.router, tags=["WMS AI Assistant"])
