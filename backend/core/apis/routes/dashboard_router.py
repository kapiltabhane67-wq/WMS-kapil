from fastapi import APIRouter, Depends

from core.apis.dependencies import current_user
from core.database.connection import db_connection
from core.schemas import UserContext
from core.services.wms_service import dashboard_summary, manager_console


router = APIRouter()


@router.get("/v1/dashboard")
def dashboard(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return dashboard_summary(conn, user)


@router.get("/v1/manager/console")
def manager_console_view(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return manager_console(conn, user)
