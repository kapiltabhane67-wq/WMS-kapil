from typing import Annotated

from fastapi import APIRouter, Depends, Path

from core.apis.dependencies import current_user
from core.database.connection import db_connection
from core.controllers import org_admin_controller
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


router = APIRouter()


@router.post("/v1/admin/sellers")
def admin_create_seller(payload: SellerCreateIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return org_admin_controller.admin_create_seller(conn, user, payload)


@router.patch("/v1/admin/sellers/{seller_id}")
def admin_update_seller(
    seller_id: Annotated[int, Path(gt=0)],
    payload: SellerUpdateIn,
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return org_admin_controller.admin_update_seller(conn, user, seller_id, payload)


@router.post("/v1/admin/warehouses")
def admin_create_warehouse(payload: WarehouseCreateIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return org_admin_controller.admin_create_warehouse(conn, user, payload)


@router.patch("/v1/admin/warehouses/{warehouse_id}")
def admin_update_warehouse(
    warehouse_id: Annotated[int, Path(gt=0)],
    payload: WarehouseUpdateIn,
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return org_admin_controller.admin_update_warehouse(conn, user, warehouse_id, payload)


@router.post("/v1/admin/bins")
def admin_create_bin(payload: BinCreateIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return org_admin_controller.admin_create_bin(conn, user, payload)


@router.patch("/v1/admin/bins/{bin_id}")
def admin_update_bin(
    bin_id: Annotated[int, Path(gt=0)],
    payload: BinUpdateIn,
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return org_admin_controller.admin_update_bin(conn, user, bin_id, payload)


@router.post("/v1/admin/products")
def admin_create_product(payload: ProductCreateIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return org_admin_controller.admin_create_product(conn, user, payload)


@router.patch("/v1/admin/products/{product_id}")
def admin_update_product(
    product_id: Annotated[int, Path(gt=0)],
    payload: ProductUpdateIn,
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return org_admin_controller.admin_update_product(conn, user, product_id, payload)


@router.post("/v1/admin/users")
def admin_create_user(payload: UserCreateIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return org_admin_controller.admin_create_user(conn, user, payload)


@router.patch("/v1/admin/users/{target_user_id}")
def admin_update_user(
    target_user_id: Annotated[int, Path(gt=0)],
    payload: UserUpdateIn,
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return org_admin_controller.admin_update_user(conn, user, target_user_id, payload)


@router.post("/v1/admin/users/{target_user_id}/active")
def admin_set_user_active(
    target_user_id: Annotated[int, Path(gt=0)],
    payload: UserActiveIn,
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return org_admin_controller.admin_set_user_active(conn, user, target_user_id, payload)


@router.post("/v1/admin/users/{target_user_id}/reset-password")
def admin_reset_user_password(
    target_user_id: Annotated[int, Path(gt=0)],
    payload: UserPasswordResetIn,
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return org_admin_controller.admin_reset_user_password(conn, user, target_user_id, payload)


@router.get("/v1/admin/audit-logs")
def admin_audit_logs(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return org_admin_controller.admin_audit_logs(conn, user)


@router.get("/v1/admin/settings")
def admin_settings(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return org_admin_controller.admin_settings(conn, user)


@router.put("/v1/admin/settings")
def admin_update_settings(payload: SettingsUpdateIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return org_admin_controller.admin_update_settings(conn, user, payload)


@router.get("/v1/admin/reports/{report_name}.csv")
def admin_export_report(
    report_name: Annotated[str, Path(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")],
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return org_admin_controller.admin_export_report(conn, user, report_name)
