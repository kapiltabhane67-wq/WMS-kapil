from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.apis.routes import (
    admin_router,
    auth_router,
    dashboard_router,
    document_router,
    fulfillment_router,
    inventory_router,
    order_router,
    receiving_router,
)
from core.database.connection import db_connection, init_db
from core.database.seed import seed_if_empty


app = FastAPI(title="Whitfield WMS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3001", "http://localhost:3001"],
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


app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(dashboard_router.router)
app.include_router(receiving_router.router)
app.include_router(inventory_router.router)
app.include_router(order_router.router)
app.include_router(fulfillment_router.router)
app.include_router(document_router.router)
