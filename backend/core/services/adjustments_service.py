from fastapi import HTTPException
from sqlite3 import Connection

from commons.auth import require_role, require_warehouse_access
from core.schemas import InventoryAdjustmentIn, UserContext
from core.services.common import audit, get_bin, get_by_code, get_product
from core.services.inventory_service import ensure_balance, record_movement

def adjust_inventory(conn: Connection, user: UserContext, payload: InventoryAdjustmentIn):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER"})
    if not payload.reason.strip():
        raise HTTPException(status_code=422, detail="Adjustment reason is required")
    seller = get_by_code(conn, "sellers", payload.seller_code)
    warehouse = get_by_code(conn, "warehouses", payload.warehouse_code)
    require_warehouse_access(user, warehouse["id"])
    product = get_product(conn, seller["id"], payload.sku)
    bin_row = get_bin(conn, warehouse["id"], payload.bin_code)
    ensure_balance(conn, seller["id"], product["id"], warehouse["id"], bin_row["id"])
    balance = conn.execute(
        """
        SELECT * FROM inventory_balances
        WHERE seller_id = ? AND product_id = ? AND warehouse_id = ? AND bin_id = ?
        """,
        (seller["id"], product["id"], warehouse["id"], bin_row["id"]),
    ).fetchone()
    if balance["good_qty"] + payload.quantity_delta < balance["reserved_qty"]:
        raise HTTPException(status_code=409, detail="Adjustment would make available stock negative")
    conn.execute(
        """
        UPDATE inventory_balances
        SET good_qty = good_qty + ?
        WHERE seller_id = ? AND product_id = ? AND warehouse_id = ? AND bin_id = ?
        """,
        (payload.quantity_delta, seller["id"], product["id"], warehouse["id"], bin_row["id"]),
    )
    record_movement(
        conn, user, "ADJUSTED", seller["id"], product["id"], warehouse["id"], bin_row["id"],
        abs(payload.quantity_delta), payload.quantity_delta, 0, payload.reason, "manual_adjustment", None,
    )
    audit(conn, user, "ADJUST_INVENTORY", "inventory_balance", balance["id"], payload.model_dump())
    return {"status": "ADJUSTED"}
