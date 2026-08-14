"""Inventory read/write flow shared by permitted roles."""

from sqlite3 import Connection

from core.schemas import InventoryAdjustmentIn, UserContext
from core.services.adjustments_service import adjust_inventory
from core.services.views_service import inventory_view, movement_view


def inventory_rows(conn: Connection, user: UserContext, seller_code: str | None = None):
    return inventory_view(conn, user, seller_code)


def inventory_movements(conn: Connection, user: UserContext):
    return movement_view(conn, user)


def inventory_adjustment(conn: Connection, user: UserContext, payload: InventoryAdjustmentIn):
    return adjust_inventory(conn, user, payload)

