from fastapi import APIRouter, Depends

from core.apis.dependencies import current_user
from core.database.connection import db_connection
from core.schemas import UserContext
from core.services.wms_service import document_view


router = APIRouter()


@router.get("/v1/documents")
def documents(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return document_view(conn, user)
