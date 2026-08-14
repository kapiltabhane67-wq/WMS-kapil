from fastapi import Header, HTTPException

from commons.auth import load_user_by_token
from core.database.connection import db_connection
from core.schemas import UserContext


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token:
            return token
    raise HTTPException(status_code=401, detail="Login token is required")


def current_user(token: str = Header(default=None, alias="Authorization")) -> UserContext:
    actual_token = bearer_token(token)
    with db_connection() as conn:
        return load_user_by_token(conn, actual_token)
