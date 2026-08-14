from fastapi import HTTPException
from sqlite3 import Connection
import hashlib
import hmac
import secrets

from core.cruds import user_crud
from core.database.connection import row_to_dict
from core.schemas import UserContext

PASSWORD_ITERATIONS = 180000


def hash_password(password: str, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_value.encode("utf-8"), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt_value}${digest.hex()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations))
    return hmac.compare_digest(digest.hex(), expected)


def load_user(conn: Connection, email: str) -> UserContext:
    row = user_crud.get_active_user_by_email(conn, email)
    if not row:
        raise HTTPException(status_code=401, detail="Unknown or inactive user")
    data = row_to_dict(row)
    data.pop("password_hash", None)
    data.pop("active", None)
    data["warehouse_ids"] = user_crud.list_user_warehouse_ids(conn, row["id"])
    return UserContext(**data)


def load_user_by_token(conn: Connection, token: str) -> UserContext:
    row = conn.execute(
        """
        SELECT u.email
        FROM auth_sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND u.active = 1
        """,
        (token,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return load_user(conn, row["email"])


def login_user(conn: Connection, email: str, password: str):
    row = user_crud.get_active_user_by_email(conn, email)
    if not row or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO auth_sessions (token, user_id) VALUES (?, ?)", (token, row["id"]))
    return {"access_token": token, "token_type": "bearer", "user": load_user(conn, email)}


def require_role(user: UserContext, roles: set[str]):
    if user.role not in roles:
        raise HTTPException(status_code=403, detail=f"{user.role} cannot perform this action")


def require_warehouse_access(user: UserContext, warehouse_id: int):
    if user.role == "ORG_ADMIN":
        return
    if warehouse_id not in user.warehouse_ids:
        raise HTTPException(status_code=403, detail="User does not have access to this warehouse")


def require_seller_access(user: UserContext, seller_id: int):
    if user.role == "ORG_ADMIN":
        return
    if user.role == "SELLER_VIEWER" and user.seller_id == seller_id:
        return
    if user.role != "SELLER_VIEWER":
        return
    raise HTTPException(status_code=403, detail="Seller user can only view their own data")
