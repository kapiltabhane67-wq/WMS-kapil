from sqlite3 import Connection

from fastapi import HTTPException

from commons.auth import hash_password, require_role
from core.cruds import user_crud
from core.models.user_model import WAREHOUSE_ROLES, UserRole
from core.schemas import UserActiveIn, UserContext, UserCreateIn, UserPasswordResetIn, UserUpdateIn
from core.services.common import audit, get_by_code
from core.utils.email import build_welcome_email


def _seller_id_for_role(conn: Connection, role: str, seller_code: str | None) -> int | None:
    if role != UserRole.SELLER_VIEWER.value:
        return None
    if not seller_code:
        raise HTTPException(status_code=422, detail="Seller viewer must be assigned to a seller")
    return int(get_by_code(conn, "sellers", seller_code)["id"])


def _warehouse_ids_for_role(conn: Connection, role: str, warehouse_codes: list[str]) -> list[int]:
    if role not in WAREHOUSE_ROLES:
        return []
    if not warehouse_codes:
        raise HTTPException(status_code=422, detail="Warehouse role must be assigned to at least one warehouse")
    return [int(get_by_code(conn, "warehouses", code)["id"]) for code in warehouse_codes]


def create_user(conn: Connection, user: UserContext, payload: UserCreateIn):
    require_role(user, {"ORG_ADMIN"})
    seller_id = _seller_id_for_role(conn, payload.role, payload.seller_code)
    warehouse_ids = _warehouse_ids_for_role(conn, payload.role, payload.warehouse_codes)
    clean_email = payload.email.strip().lower()
    user_id = user_crud.insert_user(
        conn,
        email=clean_email,
        full_name=payload.full_name,
        role=payload.role,
        seller_id=seller_id,
        password_hash=hash_password(payload.password),
    )
    user_crud.replace_user_warehouses(conn, user_id, warehouse_ids)
    welcome_email = build_welcome_email(email=clean_email, full_name=payload.full_name, role=payload.role)
    audit(
        conn,
        user,
        "CREATE_USER",
        "user",
        user_id,
        {"email": clean_email, "role": payload.role, "welcome_email_subject": welcome_email["subject"]},
    )
    return {"id": user_id, "email": clean_email, "role": payload.role}


def update_user(conn: Connection, user: UserContext, target_user_id: int, payload: UserUpdateIn):
    require_role(user, {"ORG_ADMIN"})
    if not user_crud.get_user_by_id(conn, target_user_id):
        raise HTTPException(status_code=404, detail="User not found")
    seller_id = _seller_id_for_role(conn, payload.role, payload.seller_code)
    warehouse_ids = _warehouse_ids_for_role(conn, payload.role, payload.warehouse_codes)
    row_count = user_crud.update_user_profile(
        conn,
        user_id=target_user_id,
        full_name=payload.full_name,
        role=payload.role,
        seller_id=seller_id,
    )
    if row_count != 1:
        raise HTTPException(status_code=404, detail="User not found")
    user_crud.replace_user_warehouses(conn, target_user_id, warehouse_ids)
    audit(conn, user, "UPDATE_USER", "user", target_user_id, payload.model_dump())
    return {"id": target_user_id, "status": "UPDATED"}


def set_user_active(conn: Connection, user: UserContext, target_user_id: int, payload: UserActiveIn):
    require_role(user, {"ORG_ADMIN"})
    if target_user_id == user.id and not payload.active:
        raise HTTPException(status_code=409, detail="Admin cannot deactivate their own account")
    row_count = user_crud.set_active(conn, target_user_id, payload.active)
    if row_count != 1:
        raise HTTPException(status_code=404, detail="User not found")
    if not payload.active:
        user_crud.delete_sessions(conn, target_user_id)
    audit(conn, user, "SET_USER_ACTIVE", "user", target_user_id, payload.model_dump())
    return {"id": target_user_id, "active": payload.active}


def reset_user_password(conn: Connection, user: UserContext, target_user_id: int, payload: UserPasswordResetIn):
    require_role(user, {"ORG_ADMIN"})
    row_count = user_crud.set_password_hash(conn, target_user_id, hash_password(payload.password))
    if row_count != 1:
        raise HTTPException(status_code=404, detail="User not found")
    user_crud.delete_sessions(conn, target_user_id)
    audit(conn, user, "RESET_USER_PASSWORD", "user", target_user_id, {"password_reset": True})
    return {"id": target_user_id, "status": "PASSWORD_RESET"}

