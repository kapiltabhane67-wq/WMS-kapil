from sqlite3 import Connection

from commons.auth import require_role
from core.schemas import UserContext
from core.services.admin_service import settings_payload
from core.services.receiving_service import list_receipts
from core.services.views_service import inventory_view, movement_view, reference_data
from core.services.orders_service import list_orders, list_pick_tasks

def dashboard_summary(conn: Connection, user: UserContext):
    inventory = inventory_view(conn, user)
    orders = []
    if user.role in {"ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER", "SELLER_VIEWER"}:
        orders = list_orders(conn, user)
    tasks = []
    if user.role in {"ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER"}:
        tasks = list_pick_tasks(conn, user)
    return {
        "available_units": sum(row["available_qty"] for row in inventory),
        "physical_good_units": sum(row["good_qty"] for row in inventory),
        "reserved_units": sum(row["reserved_qty"] for row in inventory),
        "open_orders": sum(1 for order in orders if order["status"] not in {"SHIPPED", "DELIVERED", "CANCELLED"}),
        "ready_pick_tasks": sum(1 for task in tasks if task["status"] in {"READY", "PICKING", "PICKED"}),
    }


def manager_console(conn: Connection, user: UserContext):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER"})
    threshold = int(settings_payload(conn).get("low_stock_threshold", 5))
    inventory = inventory_view(conn, user)
    orders = list_orders(conn, user)
    tasks = list_pick_tasks(conn, user)
    receipts = list_receipts(conn, user)
    movements = movement_view(conn, user)

    low_stock = [
        row
        for row in inventory
        if row["available_qty"] <= threshold and row["good_qty"] > 0
    ]
    damaged_stock = [row for row in inventory if row["damaged_qty"] > 0]
    open_orders = [
        order
        for order in orders
        if order["status"] not in {"SHIPPED", "DELIVERED", "CANCELLED"}
    ]
    awaiting_stock = [order for order in orders if order["status"] == "AWAITING_STOCK"]
    active_pick_tasks = [
        task
        for task in tasks
        if task["status"] in {"READY", "PICKING", "PICKED"}
    ]
    recent_adjustments = [
        movement
        for movement in movements
        if movement["movement_type"] == "ADJUSTED"
    ][:10]

    return {
        "low_stock_threshold": threshold,
        "warehouse_codes": [warehouse["code"] for warehouse in reference_data(conn, user)["warehouses"]],
        "counts": {
            "open_orders": len(open_orders),
            "awaiting_stock_orders": len(awaiting_stock),
            "active_pick_tasks": len(active_pick_tasks),
            "low_stock_rows": len(low_stock),
            "damaged_stock_rows": len(damaged_stock),
            "recent_receipts": len(receipts[:10]),
        },
        "low_stock": low_stock[:20],
        "damaged_stock": damaged_stock[:20],
        "open_orders": open_orders[:20],
        "active_pick_tasks": active_pick_tasks[:20],
        "recent_receipts": receipts[:10],
        "recent_adjustments": recent_adjustments,
    }


