from typing import Annotated

from fastapi import APIRouter, Depends, Path

from core.apis.dependencies import current_user
from core.database.connection import db_connection
from core.schemas import OrderImportIn, UserContext
from core.services.wms_service import get_order, import_order, list_orders


router = APIRouter()


@router.post("/v1/orders/import")
def marketplace_order_import(payload: OrderImportIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return import_order(conn, user, payload)


@router.get("/v1/orders")
def orders(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return list_orders(conn, user)


@router.get("/v1/orders/{order_id}")
def order_detail(order_id: Annotated[int, Path(gt=0)], user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return get_order(conn, user, order_id)
