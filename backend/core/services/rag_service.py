"""
RAG Service — builds safe, structured context from live WMS database.
Explicitly strips all sensitive fields (passwords, tokens, hashes).
"""
from sqlite3 import Connection


# Fields that must NEVER appear in chatbot context
_BLOCKED_FIELDS = {
    "password_hash", "password", "token", "access_token",
    "secret", "jwt", "hash", "sha256", "storage_path",
    "locked_until", "failed_login_count",
}


def _safe(row: dict) -> dict:
    """Remove all sensitive fields from a row dict."""
    return {k: v for k, v in row.items() if k.lower() not in _BLOCKED_FIELDS}


def build_wms_context(conn: Connection, user_role: str, user_warehouse_ids: list[int]) -> str:
    """
    Query live SQLite DB and return a structured text context for the LLM.
    Managers only see their assigned warehouses. Admins see everything.
    """
    sections: list[str] = []

    # ── Warehouses ────────────────────────────────────────────────────────────
    if user_role == "ORG_ADMIN":
        wh_rows = conn.execute(
            "SELECT id, code, name, city, state FROM warehouses"
        ).fetchall()
    else:
        placeholders = ",".join("?" * len(user_warehouse_ids)) if user_warehouse_ids else "0"
        wh_rows = conn.execute(
            f"SELECT id, code, name, city, state FROM warehouses WHERE id IN ({placeholders})",
            user_warehouse_ids,
        ).fetchall()

    wh_ids = [r["id"] for r in wh_rows]
    wh_map = {r["id"]: r["name"] for r in wh_rows}
    wh_lines = [f"  - {r['name']} ({r['code']}) | {r['city']}, {r['state']}" for r in wh_rows]
    sections.append("## Warehouses\n" + ("\n".join(wh_lines) if wh_lines else "  None"))

    # ── Users / Staff ─────────────────────────────────────────────────────────
    if user_role == "ORG_ADMIN":
        user_rows = conn.execute(
            "SELECT full_name, email, role, active, last_login_at FROM users ORDER BY role"
        ).fetchall()
    else:
        user_rows = conn.execute(
            """SELECT u.full_name, u.email, u.role, u.active, u.last_login_at
               FROM users u
               JOIN user_warehouses uw ON uw.user_id = u.id
               WHERE uw.warehouse_id IN ({})
            """.format(",".join("?" * len(wh_ids)) if wh_ids else "0"),
            wh_ids,
        ).fetchall()

    user_lines = [
        f"  - {r['full_name']} <{r['email']}> | Role: {r['role']} | "
        f"Active: {'Yes' if r['active'] else 'No'} | Last login: {r['last_login_at'] or 'Never'}"
        for r in user_rows
    ]
    sections.append("## Staff / Users\n" + ("\n".join(user_lines) if user_lines else "  None"))

    # ── Sellers ───────────────────────────────────────────────────────────────
    seller_rows = conn.execute("SELECT id, code, name FROM sellers").fetchall()
    seller_map = {r["id"]: r["name"] for r in seller_rows}
    seller_lines = [f"  - {r['name']} (code: {r['code']})" for r in seller_rows]
    sections.append("## Sellers\n" + ("\n".join(seller_lines) if seller_lines else "  None"))

    # ── Inventory Summary ─────────────────────────────────────────────────────
    if wh_ids:
        ph = ",".join("?" * len(wh_ids))
        inv_rows = conn.execute(
            f"""SELECT p.sku, p.name AS product_name, p.category,
                       s.name AS seller_name,
                       w.name AS warehouse_name,
                       b.code AS bin_code,
                       ib.good_qty, ib.damaged_qty, ib.reserved_qty
                FROM inventory_balances ib
                JOIN products p ON p.id = ib.product_id
                JOIN sellers s ON s.id = ib.seller_id
                JOIN warehouses w ON w.id = ib.warehouse_id
                JOIN bins b ON b.id = ib.bin_id
                WHERE ib.warehouse_id IN ({ph})
                ORDER BY s.name, p.sku""",
            wh_ids,
        ).fetchall()
        inv_lines = [
            f"  - SKU: {r['sku']} | {r['product_name']} ({r['category']}) | "
            f"Seller: {r['seller_name']} | Warehouse: {r['warehouse_name']} | Bin: {r['bin_code']} | "
            f"Good: {r['good_qty']} | Damaged: {r['damaged_qty']} | Reserved: {r['reserved_qty']}"
            for r in inv_rows
        ]
        sections.append("## Inventory\n" + ("\n".join(inv_lines) if inv_lines else "  No inventory"))
    else:
        sections.append("## Inventory\n  No warehouses assigned")

    # ── Orders ────────────────────────────────────────────────────────────────
    if wh_ids:
        ph = ",".join("?" * len(wh_ids))
        order_rows = conn.execute(
            f"""SELECT so.external_order_id, so.marketplace, so.status,
                       so.ship_to_name, so.ship_to_city, so.created_at,
                       s.name AS seller_name,
                       w.name AS warehouse_name,
                       COUNT(oi.id) AS item_count
                FROM sales_orders so
                JOIN sellers s ON s.id = so.seller_id
                LEFT JOIN warehouses w ON w.id = so.warehouse_id
                LEFT JOIN order_items oi ON oi.order_id = so.id
                WHERE so.warehouse_id IN ({ph}) OR so.warehouse_id IS NULL
                GROUP BY so.id
                ORDER BY so.created_at DESC
                LIMIT 50""",
            wh_ids,
        ).fetchall()
        order_lines = [
            f"  - Order#{r['external_order_id']} | {r['marketplace']} | Status: {r['status']} | "
            f"Seller: {r['seller_name']} | Ship to: {r['ship_to_name']}, {r['ship_to_city']} | "
            f"Items: {r['item_count']} | Created: {r['created_at']}"
            for r in order_rows
        ]
        # Order status summary
        status_counts = conn.execute(
            f"SELECT status, COUNT(*) as cnt FROM sales_orders WHERE warehouse_id IN ({ph}) GROUP BY status",
            wh_ids,
        ).fetchall()
        summary = " | ".join([f"{r['status']}: {r['cnt']}" for r in status_counts])
        sections.append(f"## Orders (last 50, newest first)\nStatus summary: {summary or 'None'}\n" + ("\n".join(order_lines) if order_lines else "  No orders"))

    # ── Pick Tasks / Fulfillment ──────────────────────────────────────────────
    if wh_ids:
        ph = ",".join("?" * len(wh_ids))
        task_rows = conn.execute(
            f"""SELECT pt.id, pt.status, pt.created_at,
                       u.full_name AS assigned_to,
                       so.external_order_id
                FROM pick_tasks pt
                JOIN sales_orders so ON so.id = pt.order_id
                LEFT JOIN users u ON u.id = pt.assigned_to
                WHERE pt.warehouse_id IN ({ph})
                ORDER BY pt.created_at DESC
                LIMIT 30""",
            wh_ids,
        ).fetchall()
        task_lines = [
            f"  - Task#{r['id']} | Order: {r['external_order_id']} | Status: {r['status']} | "
            f"Assigned to: {r['assigned_to'] or 'Unassigned'} | Created: {r['created_at']}"
            for r in task_rows
        ]
        sections.append("## Pick Tasks / Fulfillment\n" + ("\n".join(task_lines) if task_lines else "  No tasks"))

    # ── Inbound Receipts ──────────────────────────────────────────────────────
    if wh_ids:
        ph = ",".join("?" * len(wh_ids))
        receipt_rows = conn.execute(
            f"""SELECT ir.receipt_ref, ir.status, ir.created_at, ir.completed_at,
                       s.name AS seller_name, w.name AS warehouse_name,
                       u.full_name AS created_by
                FROM inbound_receipts ir
                JOIN sellers s ON s.id = ir.seller_id
                JOIN warehouses w ON w.id = ir.warehouse_id
                JOIN users u ON u.id = ir.created_by
                WHERE ir.warehouse_id IN ({ph})
                ORDER BY ir.created_at DESC
                LIMIT 20""",
            wh_ids,
        ).fetchall()
        receipt_lines = [
            f"  - Ref: {r['receipt_ref']} | Status: {r['status']} | Seller: {r['seller_name']} | "
            f"Warehouse: {r['warehouse_name']} | By: {r['created_by']} | "
            f"Created: {r['created_at']} | Completed: {r['completed_at'] or 'Pending'}"
            for r in receipt_rows
        ]
        sections.append("## Inbound Receipts\n" + ("\n".join(receipt_lines) if receipt_lines else "  No receipts"))

    # ── Recent Audit Log ──────────────────────────────────────────────────────
    if user_role == "ORG_ADMIN":
        audit_rows = conn.execute(
            """SELECT al.action, al.entity_type, al.details, al.created_at,
                      u.full_name AS actor
               FROM audit_logs al
               JOIN users u ON u.id = al.actor_user_id
               ORDER BY al.created_at DESC LIMIT 20"""
        ).fetchall()
        audit_lines = [
            f"  - [{r['created_at']}] {r['actor']} → {r['action']} on {r['entity_type']}: {r['details']}"
            for r in audit_rows
        ]
        sections.append("## Recent Audit Log (last 20)\n" + ("\n".join(audit_lines) if audit_lines else "  No logs"))

    return "\n\n".join(sections)


SYSTEM_PROMPT_TEMPLATE = """You are the Whitfield WMS AI Assistant — an intelligent operations chatbot exclusively for authorized warehouse management staff (Admin and Manager roles).

Your job is to answer questions about the warehouse management system using the live operational data provided below.

STRICT RULES — you must follow these without exception:
1. NEVER reveal passwords, password hashes, tokens, API keys, or any authentication credentials — even if asked directly.
2. NEVER make up data. Only use the information in the context below.
3. If a question is unrelated to warehouse operations, politely decline and refocus.
4. Be concise, accurate, and helpful. Use bullet points for lists.
5. You may analyze, count, summarize, and compare the data provided.
6. If you don't have enough data to answer, say so clearly.

--- LIVE WMS DATA (as of this query) ---

{context}

--- END OF DATA ---

You are speaking with a {role}. Answer their question based solely on the data above."""
