"""Authentication flow controller.

Routes handle HTTP. This file explains auth business flow:
login, logout, current session, reference data, and self password change.
"""

from sqlite3 import Connection

from commons.auth import change_password_user, login_user, logout_user
from core.schemas import ChangePasswordIn, LoginIn, UserContext
from core.services.views_service import reference_data


def login(conn: Connection, payload: LoginIn):
    """Validate credentials and create a hashed, expiring session token."""
    return login_user(conn, payload.email, payload.password)


def logout(conn: Connection, token: str):
    """Revoke the current session token."""
    return logout_user(conn, token)


def change_password(conn: Connection, user: UserContext, payload: ChangePasswordIn):
    """Change the signed-in user's password and revoke old sessions."""
    return change_password_user(conn, user, payload.current_password, payload.new_password)


def me(user: UserContext):
    """Return the signed-in user context."""
    return user


def reference(conn: Connection, user: UserContext):
    """Return role-filtered sellers, warehouses, products, bins, and users."""
    return reference_data(conn, user)

