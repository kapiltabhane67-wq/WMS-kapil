from fastapi import HTTPException, Response
from sqlite3 import Connection
import csv
from io import StringIO
import json

from commons.auth import hash_password, require_role, require_seller_access, require_warehouse_access
from core.database.connection import row_to_dict, rows_to_dicts
from core.schemas import (
    InventoryAdjustmentIn,
    BinCreateIn,
    BinUpdateIn,
    OrderImportIn,
    PackIn,
    PickScanIn,
    ProductCreateIn,
    ProductUpdateIn,
    ReceiptCompleteIn,
    SellerCreateIn,
    SellerUpdateIn,
    SettingsUpdateIn,
    UserContext,
    UserActiveIn,
    UserCreateIn,
    UserPasswordResetIn,
    UserUpdateIn,
    WarehouseCreateIn,
    WarehouseUpdateIn,
)


def audit(conn: Connection, user: UserContext, action: str, entity_type: str, entity_id: int | None, details: dict):
    conn.execute(
        """
        INSERT INTO audit_logs (actor_user_id, action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user.id, action, entity_type, entity_id, json.dumps(details, sort_keys=True)),
    )


def get_by_code(conn: Connection, table: str, code: str):
    row = conn.execute(f"SELECT * FROM {table} WHERE code = ?", (code,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"{table[:-1].title()} not found: {code}")
    return row


def get_product(conn: Connection, seller_id: int, sku: str):
    row = conn.execute(
        "SELECT * FROM products WHERE seller_id = ? AND sku = ?",
        (seller_id, sku),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"SKU not found for seller: {sku}")
    return row


def get_bin(conn: Connection, warehouse_id: int, bin_code: str):
    row = conn.execute(
        "SELECT * FROM bins WHERE warehouse_id = ? AND code = ?",
        (warehouse_id, bin_code),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Bin not found in warehouse: {bin_code}")
    return row


def normalize_code(value: str) -> str:
    return value.strip().upper().replace(" ", "-")


