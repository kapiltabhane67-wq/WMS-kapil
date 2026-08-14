from sqlite3 import Connection

from core.database.connection import rows_to_dicts
from core.schemas import UserContext

def document_view(conn: Connection, user: UserContext):
    where = ""
    params: list[object] = []
    if user.role == "SELLER_VIEWER":
        where = """
        WHERE EXISTS (
            SELECT 1 FROM sales_orders so
            WHERE so.id = d.reference_id AND d.reference_type = 'sales_order' AND so.seller_id = ?
        )
        OR EXISTS (
            SELECT 1 FROM shipments sh
            JOIN sales_orders so ON so.id = sh.order_id
            WHERE sh.id = d.reference_id AND d.reference_type = 'shipment' AND so.seller_id = ?
        )
        OR EXISTS (
            SELECT 1 FROM inbound_receipts ir
            WHERE ir.id = d.reference_id AND d.reference_type = 'inbound_receipt' AND ir.seller_id = ?
        )
        """
        params.extend([user.seller_id, user.seller_id, user.seller_id])
    elif user.role != "ORG_ADMIN":
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        where = f"""
        WHERE EXISTS (
            SELECT 1 FROM sales_orders so
            WHERE so.id = d.reference_id AND d.reference_type = 'sales_order'
              AND so.warehouse_id IN ({placeholders})
        )
        OR EXISTS (
            SELECT 1 FROM shipments sh
            JOIN sales_orders so ON so.id = sh.order_id
            WHERE sh.id = d.reference_id AND d.reference_type = 'shipment'
              AND so.warehouse_id IN ({placeholders})
        )
        OR EXISTS (
            SELECT 1 FROM inbound_receipts ir
            WHERE ir.id = d.reference_id AND d.reference_type = 'inbound_receipt'
              AND ir.warehouse_id IN ({placeholders})
        )
        """
        params.extend(user.warehouse_ids)
        params.extend(user.warehouse_ids)
        params.extend(user.warehouse_ids)
    rows = conn.execute(
        f"""
        SELECT d.id, d.document_type, d.reference_type, d.reference_id, d.file_name, d.status, d.created_at
        FROM documents d
        {where}
        ORDER BY d.id DESC
        LIMIT 100
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)

