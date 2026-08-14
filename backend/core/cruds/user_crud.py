from sqlite3 import Connection, Row

from core.cruds.base import execute, fetch_all, fetch_one


def get_active_user_by_email(conn: Connection, email: str) -> Row | None:
    return fetch_one(
        conn,
        """
        SELECT
            id,
            email,
            full_name,
            role,
            seller_id,
            password_hash,
            active,
            failed_login_count,
            locked_until,
            last_login_at,
            password_changed_at
        FROM users
        WHERE email = ? AND active = 1
        """,
        (email.strip().lower(),),
    )


def get_user_by_id(conn: Connection, user_id: int) -> Row | None:
    return fetch_one(
        conn,
        """
        SELECT
            id,
            email,
            full_name,
            role,
            seller_id,
            password_hash,
            active,
            failed_login_count,
            locked_until,
            last_login_at,
            password_changed_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )


def list_user_warehouse_ids(conn: Connection, user_id: int) -> list[int]:
    rows = fetch_all(conn, "SELECT warehouse_id FROM user_warehouses WHERE user_id = ?", (user_id,))
    return [row["warehouse_id"] for row in rows]


def insert_user(
    conn: Connection,
    *,
    email: str,
    full_name: str,
    role: str,
    seller_id: int | None,
    password_hash: str,
) -> int:
    cursor = execute(
        conn,
        """
        INSERT INTO users (email, full_name, role, seller_id, password_hash, password_changed_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (email.strip().lower(), full_name.strip(), role, seller_id, password_hash),
    )
    return int(cursor.lastrowid)


def update_user_profile(
    conn: Connection,
    *,
    user_id: int,
    full_name: str,
    role: str,
    seller_id: int | None,
) -> int:
    cursor = execute(
        conn,
        "UPDATE users SET full_name = ?, role = ?, seller_id = ? WHERE id = ?",
        (full_name.strip(), role, seller_id, user_id),
    )
    return cursor.rowcount


def clear_user_warehouses(conn: Connection, user_id: int) -> None:
    execute(conn, "DELETE FROM user_warehouses WHERE user_id = ?", (user_id,))


def add_user_warehouse(conn: Connection, user_id: int, warehouse_id: int) -> None:
    execute(
        conn,
        "INSERT INTO user_warehouses (user_id, warehouse_id) VALUES (?, ?)",
        (user_id, warehouse_id),
    )


def replace_user_warehouses(conn: Connection, user_id: int, warehouse_ids: list[int]) -> None:
    clear_user_warehouses(conn, user_id)
    for warehouse_id in warehouse_ids:
        add_user_warehouse(conn, user_id, warehouse_id)


def set_active(conn: Connection, user_id: int, active: bool) -> int:
    cursor = execute(conn, "UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id))
    return cursor.rowcount


def set_password_hash(conn: Connection, user_id: int, password_hash: str) -> int:
    cursor = execute(
        conn,
        """
        UPDATE users
        SET password_hash = ?, password_changed_at = CURRENT_TIMESTAMP, failed_login_count = 0, locked_until = NULL
        WHERE id = ?
        """,
        (password_hash, user_id),
    )
    return cursor.rowcount


def delete_sessions(conn: Connection, user_id: int) -> None:
    execute(conn, "UPDATE auth_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE user_id = ? AND revoked_at IS NULL", (user_id,))


def increment_failed_login(conn: Connection, user_id: int, locked_until: str | None) -> None:
    execute(
        conn,
        """
        UPDATE users
        SET failed_login_count = failed_login_count + 1, locked_until = COALESCE(?, locked_until)
        WHERE id = ?
        """,
        (locked_until, user_id),
    )


def reset_login_security_state(conn: Connection, user_id: int, login_at: str) -> None:
    execute(
        conn,
        """
        UPDATE users
        SET failed_login_count = 0, locked_until = NULL, last_login_at = ?
        WHERE id = ?
        """,
        (login_at, user_id),
    )
