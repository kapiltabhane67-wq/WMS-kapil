from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.apis.dependencies import current_user
from core.controllers import inventory_controller
from core.database.connection import db_connection
from core.schemas import InventoryAdjustmentIn, UserContext


router = APIRouter()


@router.get("/v1/inventory")
def inventory(
    seller_code: Annotated[
        str | None,
        Query(min_length=2, max_length=24, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"),
    ] = None,
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        return inventory_controller.inventory_rows(conn, user, seller_code)


@router.get("/v1/inventory/movements")
def inventory_movements(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return inventory_controller.inventory_movements(conn, user)


@router.post("/v1/inventory/adjustments")
def inventory_adjustment(payload: InventoryAdjustmentIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return inventory_controller.inventory_adjustment(conn, user, payload)
