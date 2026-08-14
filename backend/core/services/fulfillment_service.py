from fastapi import HTTPException
from sqlite3 import Connection

from commons.auth import require_role, require_seller_access, require_warehouse_access
from core.database.connection import row_to_dict, rows_to_dicts
from core.schemas import PackIn, PickScanIn, UserContext
from core.services.common import audit, get_bin, get_product
from core.services.inventory_service import record_movement

def get_order(conn: Connection, user: UserContext, order_id: int):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER", "SELLER_VIEWER"})
    order = conn.execute(
        """
        SELECT so.*, s.code AS seller_code, w.code AS warehouse_code
        FROM sales_orders so
        JOIN sellers s ON s.id = so.seller_id
        LEFT JOIN warehouses w ON w.id = so.warehouse_id
        WHERE so.id = ?
        """,
        (order_id,),
    ).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    require_seller_access(user, order["seller_id"])
    if user.role not in {"ORG_ADMIN", "SELLER_VIEWER"} and order["warehouse_id"]:
        require_warehouse_access(user, order["warehouse_id"])

    items = conn.execute(
        """
        SELECT oi.id, p.sku, p.name, oi.quantity, oi.reserved_qty, oi.picked_qty, oi.shipped_qty
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    ).fetchall()
    reservations = conn.execute(
        """
        SELECT sr.id, p.sku, w.code AS warehouse_code, b.code AS bin_code, sr.quantity, sr.status
        FROM stock_reservations sr
        JOIN products p ON p.id = sr.product_id
        JOIN warehouses w ON w.id = sr.warehouse_id
        JOIN bins b ON b.id = sr.bin_id
        WHERE sr.order_id = ?
        """,
        (order_id,),
    ).fetchall()
    tasks = conn.execute("SELECT * FROM pick_tasks WHERE order_id = ?", (order_id,)).fetchall()
    shipments = conn.execute("SELECT * FROM shipments WHERE order_id = ?", (order_id,)).fetchall()
    data = row_to_dict(order)
    data["items"] = rows_to_dicts(items)
    data["reservations"] = rows_to_dicts(reservations)
    data["pick_tasks"] = rows_to_dicts(tasks)
    data["shipments"] = rows_to_dicts(shipments)
    return data


def scan_pick(conn: Connection, user: UserContext, task_id: int, payload: PickScanIn):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER"})
    task = conn.execute("SELECT * FROM pick_tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        raise HTTPException(status_code=404, detail="Pick task not found")
    require_warehouse_access(user, task["warehouse_id"])
    if task["status"] not in {"READY", "PICKING"}:
        raise HTTPException(status_code=409, detail=f"Pick task is not pickable: {task['status']}")

    order = conn.execute("SELECT * FROM sales_orders WHERE id = ?", (task["order_id"],)).fetchone()
    product = get_product(conn, order["seller_id"], payload.sku)
    bin_row = get_bin(conn, task["warehouse_id"], payload.bin_code)
    reservation = conn.execute(
        """
        SELECT sr.*, oi.picked_qty, oi.quantity
        FROM stock_reservations sr
        JOIN order_items oi ON oi.id = sr.order_item_id
        WHERE sr.order_id = ? AND sr.product_id = ? AND sr.bin_id = ? AND sr.status = 'ACTIVE'
        """,
        (task["order_id"], product["id"], bin_row["id"]),
    ).fetchone()
    if not reservation:
        raise HTTPException(status_code=409, detail="Scanned SKU/bin is not reserved for this order")
    already_picked_for_item = conn.execute(
        "SELECT picked_qty FROM order_items WHERE id = ?",
        (reservation["order_item_id"],),
    ).fetchone()["picked_qty"]
    if already_picked_for_item + payload.quantity > reservation["quantity"]:
        raise HTTPException(status_code=409, detail="Picked quantity exceeds reserved quantity")

    conn.execute("UPDATE order_items SET picked_qty = picked_qty + ? WHERE id = ?", (payload.quantity, reservation["order_item_id"]))
    conn.execute("UPDATE sales_orders SET status = 'PICKING' WHERE id = ?", (task["order_id"],))
    conn.execute("UPDATE pick_tasks SET assigned_to = COALESCE(assigned_to, ?), status = 'PICKING' WHERE id = ?", (user.id, task_id))

    remaining = conn.execute(
        """
        SELECT SUM(quantity - picked_qty) AS remaining
        FROM order_items
        WHERE order_id = ?
        """,
        (task["order_id"],),
    ).fetchone()["remaining"]
    if remaining == 0:
        conn.execute("UPDATE sales_orders SET status = 'PICKED' WHERE id = ?", (task["order_id"],))
        conn.execute("UPDATE pick_tasks SET status = 'PICKED' WHERE id = ?", (task_id,))

    audit(conn, user, "SCAN_PICK", "pick_task", task_id, payload.model_dump())
    return {"pick_task_id": task_id, "status": "PICKED" if remaining == 0 else "PICKING"}


def pack_order(conn: Connection, user: UserContext, task_id: int, payload: PackIn):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER"})
    task = conn.execute("SELECT * FROM pick_tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        raise HTTPException(status_code=404, detail="Pick task not found")
    require_warehouse_access(user, task["warehouse_id"])
    if task["status"] == "PACKED":
        shipment = conn.execute(
            "SELECT * FROM shipments WHERE order_id = ? ORDER BY id DESC LIMIT 1",
            (task["order_id"],),
        ).fetchone()
        if shipment:
            return {
                "shipment_id": shipment["id"],
                "status": shipment["status"],
                "tracking_number": shipment["tracking_number"],
                "idempotent": True,
            }
    if task["status"] != "PICKED":
        raise HTTPException(status_code=409, detail="Order must be fully picked before packing")

    order_id = task["order_id"]
    tracking = f"WMS{order_id:06d}"
    shipment_id = conn.execute(
        """
        INSERT INTO shipments
        (order_id, carrier, tracking_number, status, weight_oz, length_in, width_in, height_in)
        VALUES (?, ?, ?, 'LABEL_CREATED', ?, ?, ?, ?)
        """,
        (
            order_id,
            payload.carrier,
            tracking,
            payload.weight_oz,
            payload.length_in,
            payload.width_in,
            payload.height_in,
        ),
    ).lastrowid
    conn.execute("UPDATE pick_tasks SET status = 'PACKED' WHERE id = ?", (task_id,))
    conn.execute("UPDATE sales_orders SET status = 'LABEL_CREATED' WHERE id = ?", (order_id,))
    conn.execute(
        """
        INSERT INTO documents (document_type, reference_type, reference_id, file_name, status)
        VALUES ('INVOICE', 'sales_order', ?, ?, 'GENERATED')
        """,
        (order_id, f"invoice-{order_id}.pdf"),
    )
    conn.execute(
        """
        INSERT INTO documents (document_type, reference_type, reference_id, file_name, status)
        VALUES ('SHIPPING_LABEL', 'shipment', ?, ?, 'GENERATED')
        """,
        (shipment_id, f"label-{tracking}.pdf"),
    )
    audit(conn, user, "PACK_ORDER", "pick_task", task_id, {"shipment_id": shipment_id, **payload.model_dump()})
    return {"shipment_id": shipment_id, "status": "LABEL_CREATED", "tracking_number": tracking}


def dispatch_shipment(conn: Connection, user: UserContext, shipment_id: int):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER"})
    shipment = conn.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if shipment["status"] == "SHIPPED":
        return {"shipment_id": shipment_id, "status": "SHIPPED", "idempotent": True}

    order = conn.execute("SELECT * FROM sales_orders WHERE id = ?", (shipment["order_id"],)).fetchone()
    require_warehouse_access(user, order["warehouse_id"])
    reservations = conn.execute(
        "SELECT * FROM stock_reservations WHERE order_id = ? AND status = 'ACTIVE'",
        (order["id"],),
    ).fetchall()
    for reservation in reservations:
        cursor = conn.execute(
            """
            UPDATE inventory_balances
            SET good_qty = good_qty - ?, reserved_qty = reserved_qty - ?
            WHERE seller_id = ? AND product_id = ? AND warehouse_id = ? AND bin_id = ?
              AND good_qty >= ? AND reserved_qty >= ?
            """,
            (
                reservation["quantity"],
                reservation["quantity"],
                reservation["seller_id"],
                reservation["product_id"],
                reservation["warehouse_id"],
                reservation["bin_id"],
                reservation["quantity"],
                reservation["quantity"],
            ),
        )
        if cursor.rowcount != 1:
            raise HTTPException(status_code=409, detail="Inventory changed unexpectedly before dispatch")
        conn.execute("UPDATE stock_reservations SET status = 'SHIPPED' WHERE id = ?", (reservation["id"],))
        conn.execute(
            "UPDATE order_items SET shipped_qty = shipped_qty + ? WHERE id = ?",
            (reservation["quantity"], reservation["order_item_id"]),
        )
        record_movement(
            conn, user, "SHIPPED", reservation["seller_id"], reservation["product_id"],
            reservation["warehouse_id"], reservation["bin_id"], reservation["quantity"],
            -reservation["quantity"], -reservation["quantity"], "Physical stock deducted at dispatch",
            "shipment", shipment_id,
        )
    conn.execute("UPDATE shipments SET status = 'SHIPPED', dispatched_at = CURRENT_TIMESTAMP WHERE id = ?", (shipment_id,))
    conn.execute("UPDATE sales_orders SET status = 'SHIPPED' WHERE id = ?", (order["id"],))
    audit(conn, user, "DISPATCH_SHIPMENT", "shipment", shipment_id, {"order_id": order["id"]})
    return {"shipment_id": shipment_id, "status": "SHIPPED", "tracking_number": shipment["tracking_number"], "idempotent": False}


