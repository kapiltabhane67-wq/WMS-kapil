from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.apis.dependencies import current_user
from core.database.connection import db_connection
from core.schemas import InventoryAdjustmentIn, UserContext
from core.services.wms_service import adjust_inventory, inventory_view, movement_view


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
        return inventory_view(conn, user, seller_code)


@router.get("/v1/inventory/movements")
def inventory_movements(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return movement_view(conn, user)


@router.post("/v1/inventory/adjustments")
def inventory_adjustment(payload: InventoryAdjustmentIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return adjust_inventory(conn, user, payload)
