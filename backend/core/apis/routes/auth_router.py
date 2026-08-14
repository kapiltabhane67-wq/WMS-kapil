from fastapi import APIRouter, Depends

from commons.auth import login_user
from core.apis.dependencies import current_user
from core.database.connection import db_connection
from core.schemas import LoginIn, UserContext
from core.services.wms_service import reference_data


router = APIRouter()


@router.post("/v1/auth/login")
def login(payload: LoginIn):
    with db_connection() as conn:
        return login_user(conn, payload.email, payload.password)


@router.get("/v1/me")
def me(user: UserContext = Depends(current_user)):
    return user


@router.get("/v1/reference")
def reference(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return reference_data(conn, user)
