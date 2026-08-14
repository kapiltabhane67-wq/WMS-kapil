from typing import Annotated

from fastapi import APIRouter, Depends, Path

from core.apis.dependencies import current_user
from core.controllers import picker_packer_controller
from core.database.connection import db_connection
from core.schemas import PackIn, PickScanIn, UserContext


router = APIRouter()


@router.get("/v1/fulfillment/pick-tasks")
def pick_tasks(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return picker_packer_controller.picker_list_tasks(conn, user)


@router.post("/v1/fulfillment/pick-tasks/{task_id}/scan")
def pick_scan(task_id: Annotated[int, Path(gt=0)], payload: PickScanIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return picker_packer_controller.picker_scan_item(conn, user, task_id, payload)


@router.post("/v1/fulfillment/pick-tasks/{task_id}/pack")
def pack(task_id: Annotated[int, Path(gt=0)], payload: PackIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return picker_packer_controller.picker_pack_order(conn, user, task_id, payload)


@router.post("/v1/shipments/{shipment_id}/dispatch")
def dispatch(shipment_id: Annotated[int, Path(gt=0)], user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return picker_packer_controller.picker_dispatch_shipment(conn, user, shipment_id)
