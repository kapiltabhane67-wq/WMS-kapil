"""SELLER_VIEWER backend flow.

Seller viewer users are read-only. They can see only their own stock,
orders, tracking, documents, and movement history.
"""

from sqlite3 import Connection

from core.schemas import UserContext
from core.services.documents_service import document_view
from core.services.fulfillment_service import get_order
from core.services.orders_service import list_orders
from core.services.views_service import inventory_view, movement_view, reference_data


def seller_inventory(conn: Connection, user: UserContext, seller_code: str | None = None):
    return inventory_view(conn, user, seller_code)


def seller_movements(conn: Connection, user: UserContext):
    return movement_view(conn, user)


def seller_orders(conn: Connection, user: UserContext):
    return list_orders(conn, user)


def seller_order_detail(conn: Connection, user: UserContext, order_id: int):
    return get_order(conn, user, order_id)


def seller_documents(conn: Connection, user: UserContext):
    return document_view(conn, user)


def seller_reference(conn: Connection, user: UserContext):
    return reference_data(conn, user)
