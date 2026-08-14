from sqlite3 import Connection

from core.schemas import UserContext

def ensure_balance(conn: Connection, seller_id: int, product_id: int, warehouse_id: int, bin_id: int):
    row = conn.execute(
        """
        SELECT * FROM inventory_balances
        WHERE seller_id = ? AND product_id = ? AND warehouse_id = ? AND bin_id = ?
        """,
        (seller_id, product_id, warehouse_id, bin_id),
    ).fetchone()
    if row:
        return row
    conn.execute(
        """
        INSERT INTO inventory_balances (seller_id, product_id, warehouse_id, bin_id)
        VALUES (?, ?, ?, ?)
        """,
        (seller_id, product_id, warehouse_id, bin_id),
    )
    return conn.execute(
        """
        SELECT * FROM inventory_balances
        WHERE seller_id = ? AND product_id = ? AND warehouse_id = ? AND bin_id = ?
        """,
        (seller_id, product_id, warehouse_id, bin_id),
    ).fetchone()


def record_movement(
    conn: Connection,
    user: UserContext,
    movement_type: str,
    seller_id: int,
    product_id: int,
    warehouse_id: int,
    bin_id: int,
    quantity: int,
    physical_delta: int,
    reserved_delta: int,
    reason: str,
    reference_type: str,
    reference_id: int | None,
):
    conn.execute(
        """
        INSERT INTO inventory_movements
        (movement_type, seller_id, product_id, warehouse_id, bin_id, quantity, physical_delta,
         reserved_delta, reason, reference_type, reference_id, actor_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            movement_type,
            seller_id,
            product_id,
            warehouse_id,
            bin_id,
            quantity,
            physical_delta,
            reserved_delta,
            reason,
            reference_type,
            reference_id,
            user.id,
        ),
    )


