from fastapi import APIRouter, Depends

from core.apis.dependencies import current_user
from core.controllers import receiver_controller
from core.database.connection import db_connection
from core.schemas import ReceiptCompleteIn, UserContext


router = APIRouter()


@router.post("/v1/receiving/complete")
def complete_receiving(payload: ReceiptCompleteIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return receiver_controller.receiver_complete_receipt(conn, user, payload)


@router.get("/v1/receiving/receipts")
def receiving_history(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return receiver_controller.receiver_receiving_history(conn, user)
