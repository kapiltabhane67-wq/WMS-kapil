"""PICKER_PACKER backend flow.

Picker/Packer flow: see pick task, scan correct SKU/bin, pack parcel,
generate label/invoice, dispatch shipment, and reduce physical stock.
"""

from sqlite3 import Connection

from core.schemas import PackIn, PickScanIn, UserContext
from core.services.fulfillment_service import dispatch_shipment, pack_order, scan_pick
from core.services.orders_service import list_pick_tasks


def picker_list_tasks(conn: Connection, user: UserContext):
    return list_pick_tasks(conn, user)


def picker_scan_item(conn: Connection, user: UserContext, task_id: int, payload: PickScanIn):
    return scan_pick(conn, user, task_id, payload)


def picker_pack_order(conn: Connection, user: UserContext, task_id: int, payload: PackIn):
    return pack_order(conn, user, task_id, payload)


def picker_dispatch_shipment(conn: Connection, user: UserContext, shipment_id: int):
    return dispatch_shipment(conn, user, shipment_id)
