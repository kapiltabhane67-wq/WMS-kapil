from sqlite3 import Connection
import os

from commons.auth import hash_password


def bootstrap_admin_config():
    return {
        "email": os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@whitfieldwms.com").strip().lower(),
        "full_name": os.getenv("BOOTSTRAP_ADMIN_NAME", "Whitfield Admin").strip(),
        "password": os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "ChangeMe123!"),
    }


def should_seed_starter_data() -> bool:
    default_value = "false" if os.getenv("VERCEL") else "true"
    return os.getenv("SEED_STARTER_DATA", default_value).strip().lower() in {"1", "true", "yes", "on"}


def seed_demo_accounts(conn: Connection):
    seller_id = conn.execute(
        "INSERT OR IGNORE INTO sellers (code, name) VALUES (?, ?)",
        ("23345", "Client Seller"),
    ).lastrowid
    if not seller_id:
        seller_id = conn.execute("SELECT id FROM sellers WHERE code = ?", ("23345",)).fetchone()["id"]

    warehouse_id = conn.execute(
        "INSERT OR IGNORE INTO warehouses (code, name, city, state) VALUES (?, ?, ?, ?)",
        ("1234", "Reno Warehouse", "Reno", "NV"),
    ).lastrowid
    if not warehouse_id:
        warehouse_id = conn.execute("SELECT id FROM warehouses WHERE code = ?", ("1234",)).fetchone()["id"]

    conn.execute(
        "INSERT OR IGNORE INTO bins (warehouse_id, code, zone, rack, shelf) VALUES (?, ?, ?, ?, ?)",
        (warehouse_id, "A-01", "A", "R1", "S1"),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO products (seller_id, sku, upc, name, category)
        VALUES (?, ?, ?, ?, ?)
        """,
        (seller_id, "SKU-TSHIRT", "123456789012", "T-Shirt", "Apparel"),
    )

    demo_users = [
        ("manager@whitfieldwms.com", "Manager", "WAREHOUSE_MANAGER", None, "Manager123!", [warehouse_id]),
        ("receiver@whitfieldwms.com", "Receiver", "RECEIVER", None, "Receiver123!", [warehouse_id]),
        ("picker@whitfieldwms.com", "Picker Packer", "PICKER_PACKER", None, "Picker123!", [warehouse_id]),
        ("seller@client.example.com", "Seller Viewer", "SELLER_VIEWER", seller_id, "Seller123!", []),
    ]
    for email, full_name, role, seller_ref, password, warehouse_ids in demo_users:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            user_id = existing["id"]
            conn.execute(
                """
                UPDATE users
                SET full_name = ?, role = ?, seller_id = ?, password_hash = ?, active = 1
                WHERE id = ?
                """,
                (full_name, role, seller_ref, hash_password(password), user_id),
            )
            conn.execute("DELETE FROM user_warehouses WHERE user_id = ?", (user_id,))
        else:
            user_id = conn.execute(
                """
                INSERT INTO users (email, full_name, role, seller_id, password_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (email, full_name, role, seller_ref, hash_password(password)),
            ).lastrowid
        for user_warehouse_id in warehouse_ids:
            conn.execute(
                "INSERT OR IGNORE INTO user_warehouses (user_id, warehouse_id) VALUES (?, ?)",
                (user_id, user_warehouse_id),
            )


def seed_if_empty(conn: Connection):
    user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if user_count:
        return

    admin = bootstrap_admin_config()
    conn.execute(
        """
        INSERT INTO users (email, full_name, role, password_hash)
        VALUES (?, ?, 'ORG_ADMIN', ?)
        """,
        (admin["email"], admin["full_name"], hash_password(admin["password"])),
    )
    if should_seed_starter_data():
        seed_demo_accounts(conn)
