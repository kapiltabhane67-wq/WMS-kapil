from fastapi import Header, HTTPException

from commons.auth import load_user_by_token
from core.database.connection import db_connection
from core.schemas import UserContext


def current_user(authorization: str | None = Header(default=None)) -> UserContext:
    with db_connection() as conn:
        if authorization and authorization.lower().startswith("bearer "):
            return load_user_by_token(conn, authorization.split(" ", 1)[1].strip())
        raise HTTPException(status_code=401, detail="Login token is required")
