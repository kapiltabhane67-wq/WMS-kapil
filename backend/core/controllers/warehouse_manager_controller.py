"""WAREHOUSE_MANAGER backend flow.

The manager watches daily operations, imports/reserves orders, reviews tasks,
handles adjustments, checks low stock, and resolves warehouse exceptions.
"""

from sqlite3 import Connection

from core.schemas import InventoryAdjustmentIn, OrderImportIn, UserContext
from core.services.adjustments_service import adjust_inventory
from core.services.fulfillment_service import get_order
from core.services.manager_service import dashboard_summary, manager_console
from core.services.orders_service import import_order, list_orders


def manager_dashboard(conn: Connection, user: UserContext):
    return dashboard_summary(conn, user)


def manager_console_view(conn: Connection, user: UserContext):
    return manager_console(conn, user)


def manager_import_order(conn: Connection, user: UserContext, payload: OrderImportIn):
    return import_order(conn, user, payload)


def manager_list_orders(conn: Connection, user: UserContext):
    return list_orders(conn, user)


def manager_order_detail(conn: Connection, user: UserContext, order_id: int):
    return get_order(conn, user, order_id)


def manager_adjust_inventory(conn: Connection, user: UserContext, payload: InventoryAdjustmentIn):
    return adjust_inventory(conn, user, payload)
