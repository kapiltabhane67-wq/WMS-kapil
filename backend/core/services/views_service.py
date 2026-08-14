from sqlite3 import Connection

from commons.auth import require_role, require_seller_access
from core.database.connection import rows_to_dicts
from core.schemas import UserContext
from core.services.common import get_by_code

def inventory_view(conn: Connection, user: UserContext, seller_code: str | None = None):
    params: list[object] = []
    where: list[str] = []
    if seller_code:
        seller = get_by_code(conn, "sellers", seller_code)
        require_seller_access(user, seller["id"])
        where.append("ib.seller_id = ?")
        params.append(seller["id"])
    elif user.role == "SELLER_VIEWER":
        where.append("ib.seller_id = ?")
        params.append(user.seller_id)

    if user.role not in {"ORG_ADMIN", "SELLER_VIEWER"}:
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        where.append(f"ib.warehouse_id IN ({placeholders})")
        params.extend(user.warehouse_ids)

    where_sql = "WHERE " + " AND ".join(where) if where else ""
    rows = conn.execute(
        f"""
        SELECT s.code AS seller_code, p.sku, p.name AS product_name, w.code AS warehouse_code,
               b.code AS bin_code, ib.good_qty, ib.damaged_qty, ib.reserved_qty,
               (ib.good_qty - ib.reserved_qty) AS available_qty
        FROM inventory_balances ib
        JOIN sellers s ON s.id = ib.seller_id
        JOIN products p ON p.id = ib.product_id
        JOIN warehouses w ON w.id = ib.warehouse_id
        JOIN bins b ON b.id = ib.bin_id
        {where_sql}
        ORDER BY s.code, p.sku, w.code, b.code
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)


def movement_view(conn: Connection, user: UserContext):
    where: list[str] = []
    params: list[object] = []
    if user.role == "SELLER_VIEWER":
        where.append("im.seller_id = ?")
        params.append(user.seller_id)
    elif user.role != "ORG_ADMIN":
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        where.append(f"im.warehouse_id IN ({placeholders})")
        params.extend(user.warehouse_ids)
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    rows = conn.execute(
        f"""
        SELECT im.id, im.movement_type, s.code AS seller_code, p.sku, w.code AS warehouse_code,
               b.code AS bin_code, im.quantity, im.physical_delta, im.reserved_delta,
               im.reason, im.reference_type, im.reference_id, u.email AS actor, im.created_at
        FROM inventory_movements im
        JOIN sellers s ON s.id = im.seller_id
        JOIN products p ON p.id = im.product_id
        JOIN warehouses w ON w.id = im.warehouse_id
        JOIN bins b ON b.id = im.bin_id
        JOIN users u ON u.id = im.actor_user_id
        {where_sql}
        ORDER BY im.id DESC
        LIMIT 200
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)


def reference_data(conn: Connection, user: UserContext):
    seller_params: list[object] = []
    seller_sql = "SELECT id, code, name FROM sellers ORDER BY code"
    if user.role == "SELLER_VIEWER":
        seller_sql = "SELECT id, code, name FROM sellers WHERE id = ? ORDER BY code"
        seller_params.append(user.seller_id)
    sellers = rows_to_dicts(conn.execute(seller_sql, seller_params).fetchall())

    warehouse_params: list[object] = []
    warehouse_sql = "SELECT id, code, name, city, state FROM warehouses ORDER BY code"
    if user.role == "SELLER_VIEWER":
        warehouse_sql = """
        SELECT DISTINCT w.id, w.code, w.name, w.city, w.state
        FROM warehouses w
        WHERE EXISTS (
            SELECT 1 FROM inventory_balances ib
            WHERE ib.warehouse_id = w.id AND ib.seller_id = ?
        )
        OR EXISTS (
            SELECT 1 FROM sales_orders so
            WHERE so.warehouse_id = w.id AND so.seller_id = ?
        )
        OR EXISTS (
            SELECT 1 FROM inbound_receipts ir
            WHERE ir.warehouse_id = w.id AND ir.seller_id = ?
        )
        ORDER BY w.code
        """
        warehouse_params.extend([user.seller_id, user.seller_id, user.seller_id])
    elif user.role != "ORG_ADMIN":
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        warehouse_sql = f"SELECT id, code, name, city, state FROM warehouses WHERE id IN ({placeholders}) ORDER BY code"
        warehouse_params.extend(user.warehouse_ids)
    warehouses = rows_to_dicts(conn.execute(warehouse_sql, warehouse_params).fetchall())

    product_filter = ""
    product_params: list[object] = []
    if user.role == "SELLER_VIEWER":
        product_filter = "WHERE p.seller_id = ?"
        product_params.append(user.seller_id)
    products = rows_to_dicts(
        conn.execute(
            f"""
            SELECT p.id, s.code AS seller_code, p.sku, p.upc, p.name, p.category
            FROM products p
            JOIN sellers s ON s.id = p.seller_id
            {product_filter}
            ORDER BY s.code, p.sku
            """,
            product_params,
        ).fetchall()
    )

    bin_filter = ""
    bin_params: list[object] = []
    if user.role == "SELLER_VIEWER":
        bin_filter = """
        WHERE EXISTS (
            SELECT 1 FROM inventory_balances ib
            WHERE ib.bin_id = b.id AND ib.seller_id = ?
        )
        OR EXISTS (
            SELECT 1 FROM stock_reservations sr
            WHERE sr.bin_id = b.id AND sr.seller_id = ?
        )
        OR EXISTS (
            SELECT 1
            FROM inbound_receipts ir
            JOIN inbound_receipt_items iri ON iri.receipt_id = ir.id
            WHERE iri.bin_id = b.id AND ir.seller_id = ?
        )
        """
        bin_params.extend([user.seller_id, user.seller_id, user.seller_id])
    elif user.role != "ORG_ADMIN":
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        bin_filter = f"WHERE b.warehouse_id IN ({placeholders})"
        bin_params.extend(user.warehouse_ids)
    bins = rows_to_dicts(
        conn.execute(
            f"""
            SELECT b.id, w.code AS warehouse_code, b.code, b.zone, b.rack, b.shelf
            FROM bins b
            JOIN warehouses w ON w.id = b.warehouse_id
            {bin_filter}
            ORDER BY w.code, b.code
            """,
            bin_params,
        ).fetchall()
    )
    users: list[dict] = []
    if user.role == "ORG_ADMIN":
        users = rows_to_dicts(
            conn.execute(
                """
                SELECT u.id, u.email, u.full_name, u.role, u.active, s.code AS seller_code,
                       GROUP_CONCAT(w.code, ', ') AS warehouse_codes
                FROM users u
                LEFT JOIN sellers s ON s.id = u.seller_id
                LEFT JOIN user_warehouses uw ON uw.user_id = u.id
                LEFT JOIN warehouses w ON w.id = uw.warehouse_id
                GROUP BY u.id, u.email, u.full_name, u.role, u.active, s.code
                ORDER BY u.role, u.email
                """
            ).fetchall()
        )
    return {"sellers": sellers, "warehouses": warehouses, "products": products, "bins": bins, "users": users}


