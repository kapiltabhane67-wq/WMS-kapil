from fastapi import HTTPException
from sqlite3 import Connection
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets

from core.cruds import user_crud
from core.database.connection import row_to_dict
from core.schemas import UserContext

PASSWORD_ITERATIONS = 180000
SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", "480"))
MAX_FAILED_LOGINS = int(os.getenv("MAX_FAILED_LOGINS", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "15"))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso(moment: datetime | None = None) -> str:
    return (moment or utc_now()).isoformat(timespec="seconds")


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def log_auth_event(conn: Connection, *, email: str, user_id: int | None, event_type: str, success: bool, reason: str) -> None:
    conn.execute(
        """
        INSERT INTO auth_events (email, user_id, event_type, success, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (email.strip().lower(), user_id, event_type, 1 if success else 0, reason),
    )
    if user_id:
        conn.execute(
            """
            INSERT INTO audit_logs (actor_user_id, action, entity_type, entity_id, details)
            VALUES (?, ?, 'user', ?, ?)
            """,
            (user_id, event_type, user_id, reason),
        )


def commit_auth_security_event(conn: Connection) -> None:
    conn.commit()


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
    data.pop("failed_login_count", None)
    data.pop("locked_until", None)
    data.pop("last_login_at", None)
    data.pop("password_changed_at", None)
    data["warehouse_ids"] = user_crud.list_user_warehouse_ids(conn, row["id"])
    return UserContext(**data)


def load_user_by_token(conn: Connection, token: str) -> UserContext:
    now = utc_iso()
    row = conn.execute(
        """
        SELECT u.email, s.expires_at
        FROM auth_sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ?
          AND u.active = 1
          AND s.revoked_at IS NULL
          AND s.expires_at > ?
        """,
        (hash_token(token), now),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    conn.execute("UPDATE auth_sessions SET last_seen_at = ? WHERE token = ?", (now, hash_token(token)))
    return load_user(conn, row["email"])


def login_user(conn: Connection, email: str, password: str):
    clean_email = email.strip().lower()
    row = user_crud.get_active_user_by_email(conn, clean_email)
    if not row:
        log_auth_event(conn, email=clean_email, user_id=None, event_type="LOGIN_FAILED", success=False, reason="unknown_or_inactive_user")
        commit_auth_security_event(conn)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    locked_until = parse_utc(row["locked_until"])
    if locked_until and locked_until > utc_now():
        log_auth_event(conn, email=clean_email, user_id=row["id"], event_type="LOGIN_LOCKED", success=False, reason=f"locked_until={locked_until.isoformat()}")
        commit_auth_security_event(conn)
        raise HTTPException(status_code=423, detail="Account temporarily locked after repeated failed login attempts")
    if not verify_password(password, row["password_hash"]):
        failed_count = int(row["failed_login_count"] or 0) + 1
        next_locked_until = utc_iso(utc_now() + timedelta(minutes=LOCKOUT_MINUTES)) if failed_count >= MAX_FAILED_LOGINS else None
        user_crud.increment_failed_login(conn, row["id"], next_locked_until)
        reason = "invalid_password"
        if next_locked_until:
            reason = f"invalid_password_locked_until={next_locked_until}"
        log_auth_event(conn, email=clean_email, user_id=row["id"], event_type="LOGIN_FAILED", success=False, reason=reason)
        commit_auth_security_event(conn)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    login_at = utc_iso()
    user_crud.reset_login_security_state(conn, row["id"], login_at)
    token = secrets.token_urlsafe(32)
    expires_at = utc_iso(utc_now() + timedelta(minutes=SESSION_TTL_MINUTES))
    conn.execute(
        """
        INSERT INTO auth_sessions (token, user_id, expires_at, last_seen_at)
        VALUES (?, ?, ?, ?)
        """,
        (hash_token(token), row["id"], expires_at, login_at),
    )
    log_auth_event(conn, email=clean_email, user_id=row["id"], event_type="LOGIN_SUCCESS", success=True, reason=f"expires_at={expires_at}")
    return {"access_token": token, "token_type": "bearer", "expires_at": expires_at, "user": load_user(conn, clean_email)}


def logout_user(conn: Connection, token: str):
    cursor = conn.execute(
        "UPDATE auth_sessions SET revoked_at = ? WHERE token = ? AND revoked_at IS NULL",
        (utc_iso(), hash_token(token)),
    )
    return {"status": "LOGGED_OUT", "revoked": cursor.rowcount == 1}


def change_password_user(conn: Connection, user: UserContext, old_password: str, new_password: str):
    row = user_crud.get_user_by_id(conn, user.id)
    if not row or not verify_password(old_password, row["password_hash"]):
        log_auth_event(conn, email=user.email, user_id=user.id, event_type="CHANGE_PASSWORD_FAILED", success=False, reason="invalid_current_password")
        commit_auth_security_event(conn)
        raise HTTPException(status_code=401, detail="Invalid current password")
    user_crud.set_password_hash(conn, user.id, hash_password(new_password))
    user_crud.delete_sessions(conn, user.id)
    log_auth_event(conn, email=user.email, user_id=user.id, event_type="CHANGE_PASSWORD_SUCCESS", success=True, reason="password_changed_sessions_revoked")
    return {"status": "PASSWORD_CHANGED"}


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
