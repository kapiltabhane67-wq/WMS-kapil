from fastapi import APIRouter, Depends

from core.apis.dependencies import current_user
from core.controllers import warehouse_manager_controller
from core.database.connection import db_connection
from core.schemas import UserContext


router = APIRouter()


@router.get("/v1/dashboard")
def dashboard(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return warehouse_manager_controller.manager_dashboard(conn, user)


@router.get("/v1/manager/console")
def manager_console_view(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return warehouse_manager_controller.manager_console_view(conn, user)
