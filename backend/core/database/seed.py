from sqlite3 import Connection
import os

from commons.auth import hash_password


def bootstrap_admin_config():
    return {
        "email": os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@whitfieldwms.com").strip().lower(),
        "full_name": os.getenv("BOOTSTRAP_ADMIN_NAME", "Whitfield Admin").strip(),
        "password": os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "ChangeMe123!"),
    }


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
