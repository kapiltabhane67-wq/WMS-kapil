from fastapi import APIRouter, Depends

from core.apis.dependencies import current_user
from core.database.connection import db_connection
from core.schemas import ReceiptCompleteIn, UserContext
from core.services.wms_service import complete_receipt, list_receipts


router = APIRouter()


@router.post("/v1/receiving/complete")
def complete_receiving(payload: ReceiptCompleteIn, user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return complete_receipt(conn, user, payload)


@router.get("/v1/receiving/receipts")
def receiving_history(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return list_receipts(conn, user)
