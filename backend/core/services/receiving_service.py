from fastapi import HTTPException
from sqlite3 import Connection

from commons.auth import require_role, require_warehouse_access
from core.database.connection import rows_to_dicts
from core.schemas import ReceiptCompleteIn, UserContext
from core.services.common import audit, get_bin, get_by_code, get_product, normalize_code
from core.services.inventory_service import ensure_balance, record_movement

def complete_receipt(conn: Connection, user: UserContext, payload: ReceiptCompleteIn):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER", "RECEIVER"})
    seller = get_by_code(conn, "sellers", payload.seller_code)
    warehouse = get_by_code(conn, "warehouses", payload.warehouse_code)
    require_warehouse_access(user, warehouse["id"])

    existing = conn.execute(
        """
        SELECT * FROM inbound_receipts
        WHERE seller_id = ? AND warehouse_id = ? AND receipt_ref = ?
        """,
        (seller["id"], warehouse["id"], payload.receipt_ref),
    ).fetchone()
    if existing and existing["status"] == "COMPLETED":
        existing_items = conn.execute(
            """
            SELECT p.sku, b.code AS bin_code, iri.good_qty, iri.damaged_qty
            FROM inbound_receipt_items iri
            JOIN products p ON p.id = iri.product_id
            JOIN bins b ON b.id = iri.bin_id
            WHERE iri.receipt_id = ?
            ORDER BY p.sku, b.code
            """,
            (existing["id"],),
        ).fetchall()
        incoming_items = sorted(
            [
                {
                    "sku": item.sku,
                    "bin_code": normalize_code(item.bin_code),
                    "good_qty": item.good_qty,
                    "damaged_qty": item.damaged_qty,
                }
                for item in payload.items
            ],
            key=lambda item: (item["sku"], item["bin_code"]),
        )
        stored_items = sorted(
            [
                {
                    "sku": row["sku"],
                    "bin_code": row["bin_code"],
                    "good_qty": row["good_qty"],
                    "damaged_qty": row["damaged_qty"],
                }
                for row in existing_items
            ],
            key=lambda item: (item["sku"], item["bin_code"]),
        )
        if incoming_items != stored_items:
            raise HTTPException(status_code=409, detail="Receipt reference already completed with different item details")
        return {"receipt_id": existing["id"], "status": "COMPLETED", "idempotent": True}

    if not payload.items:
        raise HTTPException(status_code=422, detail="Receipt must contain at least one item")

    receipt_id = conn.execute(
        """
        INSERT INTO inbound_receipts (seller_id, warehouse_id, receipt_ref, status, created_by, completed_at)
        VALUES (?, ?, ?, 'COMPLETED', ?, CURRENT_TIMESTAMP)
        """,
        (seller["id"], warehouse["id"], payload.receipt_ref, user.id),
    ).lastrowid

    for item in payload.items:
        if item.good_qty == 0 and item.damaged_qty == 0:
            raise HTTPException(status_code=422, detail=f"Receipt item has no quantity: {item.sku}")
        product = get_product(conn, seller["id"], item.sku)
        bin_row = get_bin(conn, warehouse["id"], item.bin_code)
        ensure_balance(conn, seller["id"], product["id"], warehouse["id"], bin_row["id"])
        conn.execute(
            """
            INSERT INTO inbound_receipt_items (receipt_id, product_id, bin_id, good_qty, damaged_qty)
            VALUES (?, ?, ?, ?, ?)
            """,
            (receipt_id, product["id"], bin_row["id"], item.good_qty, item.damaged_qty),
        )
        if item.good_qty:
            conn.execute(
                """
                UPDATE inventory_balances
                SET good_qty = good_qty + ?
                WHERE seller_id = ? AND product_id = ? AND warehouse_id = ? AND bin_id = ?
                """,
                (item.good_qty, seller["id"], product["id"], warehouse["id"], bin_row["id"]),
            )
            record_movement(
                conn, user, "RECEIVED", seller["id"], product["id"], warehouse["id"], bin_row["id"],
                item.good_qty, item.good_qty, 0, "Good inventory received", "inbound_receipt", receipt_id,
            )
        if item.damaged_qty:
            conn.execute(
                """
                UPDATE inventory_balances
                SET damaged_qty = damaged_qty + ?
                WHERE seller_id = ? AND product_id = ? AND warehouse_id = ? AND bin_id = ?
                """,
                (item.damaged_qty, seller["id"], product["id"], warehouse["id"], bin_row["id"]),
            )
            record_movement(
                conn, user, "DAMAGED_RECEIVED", seller["id"], product["id"], warehouse["id"], bin_row["id"],
                item.damaged_qty, item.damaged_qty, 0, "Damaged inventory received", "inbound_receipt", receipt_id,
            )

    conn.execute(
        """
        INSERT INTO documents (document_type, reference_type, reference_id, file_name, status)
        VALUES ('RECEIPT', 'inbound_receipt', ?, ?, 'GENERATED')
        """,
        (receipt_id, f"receipt-{receipt_id}.pdf"),
    )
    audit(conn, user, "COMPLETE_RECEIPT", "inbound_receipt", receipt_id, payload.model_dump())
    return {"receipt_id": receipt_id, "status": "COMPLETED", "idempotent": False}


def list_receipts(conn: Connection, user: UserContext):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER", "RECEIVER"})
    where: list[str] = []
    params: list[object] = []
    if user.role != "ORG_ADMIN":
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        where.append(f"ir.warehouse_id IN ({placeholders})")
        params.extend(user.warehouse_ids)
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    rows = conn.execute(
        f"""
        SELECT ir.id, s.code AS seller_code, w.code AS warehouse_code, ir.receipt_ref,
               ir.status, u.email AS created_by, ir.completed_at,
               COALESCE(SUM(iri.good_qty), 0) AS good_qty,
               COALESCE(SUM(iri.damaged_qty), 0) AS damaged_qty
        FROM inbound_receipts ir
        JOIN sellers s ON s.id = ir.seller_id
        JOIN warehouses w ON w.id = ir.warehouse_id
        JOIN users u ON u.id = ir.created_by
        LEFT JOIN inbound_receipt_items iri ON iri.receipt_id = ir.id
        {where_sql}
        GROUP BY ir.id, s.code, w.code, ir.receipt_ref, ir.status, u.email, ir.completed_at
        ORDER BY ir.id DESC
        LIMIT 100
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)


