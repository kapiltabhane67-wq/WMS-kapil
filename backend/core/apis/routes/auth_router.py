from fastapi import APIRouter, Depends

from core.apis.dependencies import bearer_token, current_user
from core.controllers import auth_controller
from core.database.connection import db_connection
from core.schemas import ChangePasswordIn, LoginIn, UserContext


router = APIRouter()


@router.post("/v1/auth/login")
def login(payload: LoginIn):
    with db_connection() as conn:
        return auth_controller.login(conn, payload)


@router.post("/v1/auth/logout")
def logout(token: str = Depends(bearer_token)):
    with db_connection() as conn:
        return auth_controller.logout(conn, token)


@router.post("/v1/auth/change-password")
def change_password(payload: ChangePasswordIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return auth_controller.change_password(conn, user, payload)


@router.get("/v1/me")
def me(user: UserContext = Depends(current_user)):
    return auth_controller.me(user)


@router.get("/v1/reference")
def reference(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return auth_controller.reference(conn, user)
