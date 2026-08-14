from fastapi import APIRouter, Depends

from commons.auth import change_password_user, login_user, logout_user
from core.apis.dependencies import bearer_token, current_user
from core.database.connection import db_connection
from core.schemas import ChangePasswordIn, LoginIn, UserContext
from core.services.wms_service import reference_data


router = APIRouter()


@router.post("/v1/auth/login")
def login(payload: LoginIn):
    with db_connection() as conn:
        return login_user(conn, payload.email, payload.password)


@router.post("/v1/auth/logout")
def logout(token: str = Depends(bearer_token)):
    with db_connection() as conn:
        return logout_user(conn, token)


@router.post("/v1/auth/change-password")
def change_password(payload: ChangePasswordIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return change_password_user(conn, user, payload.current_password, payload.new_password)


@router.get("/v1/me")
def me(user: UserContext = Depends(current_user)):
    return user


@router.get("/v1/reference")
def reference(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return reference_data(conn, user)
