"""ORG_ADMIN backend flow.

The ORG_ADMIN owns organization setup: sellers, warehouses, bins, products,
users, permissions, settings, reports, and audit visibility.
"""

from sqlite3 import Connection

from core.controllers.user_controller import create_user, reset_user_password, set_user_active, update_user
from core.schemas import (
    BinCreateIn,
    BinUpdateIn,
    ProductCreateIn,
    ProductUpdateIn,
    SellerCreateIn,
    SellerUpdateIn,
    SettingsUpdateIn,
    UserActiveIn,
    UserContext,
    UserCreateIn,
    UserPasswordResetIn,
    UserUpdateIn,
    WarehouseCreateIn,
    WarehouseUpdateIn,
)
from core.services.admin_service import audit_log_view, export_report, get_settings, update_settings
from core.services.setup_service import (
    create_bin,
    create_product,
    create_seller,
    create_warehouse,
    update_bin,
    update_product,
    update_seller,
    update_warehouse,
)


def admin_create_seller(conn: Connection, user: UserContext, payload: SellerCreateIn):
    return create_seller(conn, user, payload)


def admin_update_seller(conn: Connection, user: UserContext, seller_id: int, payload: SellerUpdateIn):
    return update_seller(conn, user, seller_id, payload)


def admin_create_warehouse(conn: Connection, user: UserContext, payload: WarehouseCreateIn):
    return create_warehouse(conn, user, payload)


def admin_update_warehouse(conn: Connection, user: UserContext, warehouse_id: int, payload: WarehouseUpdateIn):
    return update_warehouse(conn, user, warehouse_id, payload)


def admin_create_bin(conn: Connection, user: UserContext, payload: BinCreateIn):
    return create_bin(conn, user, payload)


def admin_update_bin(conn: Connection, user: UserContext, bin_id: int, payload: BinUpdateIn):
    return update_bin(conn, user, bin_id, payload)


def admin_create_product(conn: Connection, user: UserContext, payload: ProductCreateIn):
    return create_product(conn, user, payload)


def admin_update_product(conn: Connection, user: UserContext, product_id: int, payload: ProductUpdateIn):
    return update_product(conn, user, product_id, payload)


def admin_create_user(conn: Connection, user: UserContext, payload: UserCreateIn):
    return create_user(conn, user, payload)


def admin_update_user(conn: Connection, user: UserContext, target_user_id: int, payload: UserUpdateIn):
    return update_user(conn, user, target_user_id, payload)


def admin_set_user_active(conn: Connection, user: UserContext, target_user_id: int, payload: UserActiveIn):
    return set_user_active(conn, user, target_user_id, payload)


def admin_reset_user_password(conn: Connection, user: UserContext, target_user_id: int, payload: UserPasswordResetIn):
    return reset_user_password(conn, user, target_user_id, payload)


def admin_audit_logs(conn: Connection, user: UserContext):
    return audit_log_view(conn, user)


def admin_settings(conn: Connection, user: UserContext):
    return get_settings(conn, user)


def admin_update_settings(conn: Connection, user: UserContext, payload: SettingsUpdateIn):
    return update_settings(conn, user, payload)


def admin_export_report(conn: Connection, user: UserContext, report_name: str):
    return export_report(conn, user, report_name)

