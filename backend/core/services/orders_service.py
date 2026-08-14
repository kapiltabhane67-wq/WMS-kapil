from fastapi import HTTPException
from sqlite3 import Connection
import json

from commons.auth import require_role, require_seller_access, require_warehouse_access
from core.database.connection import row_to_dict, rows_to_dicts
from core.schemas import OrderImportIn, UserContext
from core.services.common import audit, get_by_code, get_product
from core.services.inventory_service import record_movement

def list_orders(conn: Connection, user: UserContext):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER", "SELLER_VIEWER"})
    where: list[str] = []
    params: list[object] = []
    if user.role == "SELLER_VIEWER":
        where.append("so.seller_id = ?")
        params.append(user.seller_id)
    if user.role not in {"ORG_ADMIN", "SELLER_VIEWER"}:
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        where.append(f"so.warehouse_id IN ({placeholders})")
        params.extend(user.warehouse_ids)
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    rows = conn.execute(
        f"""
        SELECT so.id, s.code AS seller_code, w.code AS warehouse_code, so.marketplace,
               so.external_order_id, so.status, so.ship_to_name, so.ship_to_city,
               sh.carrier, sh.tracking_number, sh.status AS shipment_status, so.created_at
        FROM sales_orders so
        JOIN sellers s ON s.id = so.seller_id
        LEFT JOIN warehouses w ON w.id = so.warehouse_id
        LEFT JOIN shipments sh ON sh.id = (
            SELECT latest_sh.id
            FROM shipments latest_sh
            WHERE latest_sh.order_id = so.id
            ORDER BY latest_sh.id DESC
            LIMIT 1
        )
        {where_sql}
        ORDER BY so.id DESC
        LIMIT 100
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)


def list_pick_tasks(conn: Connection, user: UserContext):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER"})
    where: list[str] = []
    params: list[object] = []
    if user.role != "ORG_ADMIN":
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        where.append(f"pt.warehouse_id IN ({placeholders})")
        params.extend(user.warehouse_ids)
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    rows = conn.execute(
        f"""
        SELECT pt.id, pt.order_id, pt.status, w.code AS warehouse_code, u.email AS assigned_to,
               so.external_order_id, so.ship_to_name, so.ship_to_city,
               COALESCE(GROUP_CONCAT(p.sku || ' from ' || b.code || ' x' || sr.quantity, '; '), '') AS pick_items,
               MIN(p.sku) AS first_sku,
               MIN(b.code) AS first_bin_code,
               COALESCE(SUM(sr.quantity), 0) AS total_units,
               sh.id AS shipment_id,
               sh.carrier,
               sh.tracking_number,
               sh.status AS shipment_status
        FROM pick_tasks pt
        JOIN warehouses w ON w.id = pt.warehouse_id
        JOIN sales_orders so ON so.id = pt.order_id
        LEFT JOIN users u ON u.id = pt.assigned_to
        LEFT JOIN stock_reservations sr ON sr.order_id = pt.order_id AND sr.status = 'ACTIVE'
        LEFT JOIN products p ON p.id = sr.product_id
        LEFT JOIN bins b ON b.id = sr.bin_id
        LEFT JOIN shipments sh ON sh.id = (
            SELECT latest_sh.id
            FROM shipments latest_sh
            WHERE latest_sh.order_id = pt.order_id
            ORDER BY latest_sh.id DESC
            LIMIT 1
        )
        {where_sql}
        GROUP BY pt.id, pt.order_id, pt.status, w.code, u.email, so.external_order_id, so.ship_to_name, so.ship_to_city,
                 sh.id, sh.carrier, sh.tracking_number, sh.status
        ORDER BY CASE pt.status WHEN 'READY' THEN 1 WHEN 'PICKING' THEN 2 WHEN 'PICKED' THEN 3 ELSE 4 END, pt.id DESC
        LIMIT 100
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)


def import_order(conn: Connection, user: UserContext, payload: OrderImportIn):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER"})
    seller = get_by_code(conn, "sellers", payload.seller_code)
    warehouse = None
    if payload.preferred_warehouse_code:
        warehouse = get_by_code(conn, "warehouses", payload.preferred_warehouse_code)
        require_warehouse_access(user, warehouse["id"])

    source = f"{payload.marketplace}:{seller['code']}"
    event_id = payload.external_order_id
    existing = conn.execute(
        """
        SELECT * FROM sales_orders
        WHERE seller_id = ? AND marketplace = ? AND external_order_id = ?
        """,
        (seller["id"], payload.marketplace, payload.external_order_id),
    ).fetchone()
    if existing:
        return {"order_id": existing["id"], "status": existing["status"], "idempotent": True}

    conn.execute(
        """
        INSERT INTO integration_events (source, external_id, status, payload_summary)
        VALUES (?, ?, 'RECEIVED', ?)
        """,
        (source, event_id, json.dumps({"items": [item.model_dump() for item in payload.items]})),
    )

    order_id = conn.execute(
        """
        INSERT INTO sales_orders
        (seller_id, warehouse_id, marketplace, external_order_id, status, ship_to_name, ship_to_city)
        VALUES (?, ?, ?, ?, 'NEW', ?, ?)
        """,
        (
            seller["id"],
            warehouse["id"] if warehouse else None,
            payload.marketplace,
            payload.external_order_id,
            payload.ship_to_name,
            payload.ship_to_city,
        ),
    ).lastrowid

    for item in payload.items:
        product = get_product(conn, seller["id"], item.sku)
        conn.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity)
            VALUES (?, ?, ?)
            """,
            (order_id, product["id"], item.quantity),
        )

    reserved = reserve_order(conn, user, order_id, preferred_warehouse_id=warehouse["id"] if warehouse else None)
    audit(conn, user, "IMPORT_ORDER", "sales_order", order_id, payload.model_dump())
    return {"order_id": order_id, "status": reserved["status"], "idempotent": False}


def reserve_order(conn: Connection, user: UserContext, order_id: int, preferred_warehouse_id: int | None = None):
    order = conn.execute("SELECT * FROM sales_orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    selected_warehouse_id = preferred_warehouse_id
    for item in order_items:
        remaining = item["quantity"] - item["reserved_qty"]
        if remaining <= 0:
            continue
        product_id = item["product_id"]
        params: list[object] = [order["seller_id"], product_id]
        warehouse_sql = ""
        if selected_warehouse_id:
            warehouse_sql = "AND warehouse_id = ?"
            params.append(selected_warehouse_id)
        candidates = conn.execute(
            f"""
            SELECT * FROM inventory_balances
            WHERE seller_id = ? AND product_id = ? {warehouse_sql}
              AND (good_qty - reserved_qty) > 0
            ORDER BY (good_qty - reserved_qty) DESC
            """,
            params,
        ).fetchall()
        for balance in candidates:
            available = balance["good_qty"] - balance["reserved_qty"]
            reserve_qty = min(available, remaining)
            if reserve_qty <= 0:
                continue
            if selected_warehouse_id is None:
                selected_warehouse_id = balance["warehouse_id"]
                require_warehouse_access(user, selected_warehouse_id)
            if balance["warehouse_id"] != selected_warehouse_id:
                continue
            conn.execute(
                "UPDATE inventory_balances SET reserved_qty = reserved_qty + ? WHERE id = ?",
                (reserve_qty, balance["id"]),
            )
            conn.execute(
                "UPDATE order_items SET reserved_qty = reserved_qty + ? WHERE id = ?",
                (reserve_qty, item["id"]),
            )
            conn.execute(
                """
                INSERT INTO stock_reservations
                (order_id, order_item_id, seller_id, product_id, warehouse_id, bin_id, quantity, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
                """,
                (
                    order_id,
                    item["id"],
                    order["seller_id"],
                    product_id,
                    balance["warehouse_id"],
                    balance["bin_id"],
                    reserve_qty,
                ),
            )
            record_movement(
                conn, user, "RESERVED", order["seller_id"], product_id, balance["warehouse_id"],
                balance["bin_id"], reserve_qty, 0, reserve_qty, "Stock reserved for order",
                "sales_order", order_id,
            )
            remaining -= reserve_qty
            if remaining == 0:
                break
        if remaining:
            conn.execute("UPDATE sales_orders SET status = 'AWAITING_STOCK' WHERE id = ?", (order_id,))
            audit(conn, user, "ORDER_AWAITING_STOCK", "sales_order", order_id, {"missing_qty": remaining})
            return {"order_id": order_id, "status": "AWAITING_STOCK"}

    conn.execute(
        "UPDATE sales_orders SET status = 'RESERVED', warehouse_id = ? WHERE id = ?",
        (selected_warehouse_id, order_id),
    )
    task_id = conn.execute(
        """
        INSERT INTO pick_tasks (order_id, warehouse_id, status)
        VALUES (?, ?, 'READY')
        """,
        (order_id, selected_warehouse_id),
    ).lastrowid
    audit(conn, user, "RESERVE_ORDER", "sales_order", order_id, {"pick_task_id": task_id})
    return {"order_id": order_id, "status": "RESERVED", "pick_task_id": task_id}


