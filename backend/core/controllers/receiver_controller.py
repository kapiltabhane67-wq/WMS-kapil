"""RECEIVER backend flow.

Receiver flow: incoming stock arrives, receiver scans product/bin,
records good/damaged quantities, and the inventory ledger is updated.
"""

from sqlite3 import Connection

from core.schemas import ReceiptCompleteIn, UserContext
from core.services.receiving_service import complete_receipt, list_receipts


def receiver_complete_receipt(conn: Connection, user: UserContext, payload: ReceiptCompleteIn):
    return complete_receipt(conn, user, payload)


def receiver_receiving_history(conn: Connection, user: UserContext):
    return list_receipts(conn, user)

