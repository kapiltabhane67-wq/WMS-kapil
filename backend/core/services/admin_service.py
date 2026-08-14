from fastapi import HTTPException, Response
from sqlite3 import Connection
import csv
from io import StringIO
import json

from commons.auth import require_role
from core.database.connection import rows_to_dicts
from core.schemas import SettingsUpdateIn, UserContext
from core.services.common import audit
from core.services.receiving_service import list_receipts
from core.services.views_service import inventory_view, movement_view
from core.services.orders_service import list_orders

def settings_payload(conn: Connection):
    rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    data = {row["key"]: json.loads(row["value"]) for row in rows}
    defaults = SettingsUpdateIn().model_dump()
    defaults.update(data)
    return defaults


def get_settings(conn: Connection, user: UserContext):
    require_role(user, {"ORG_ADMIN"})
    return settings_payload(conn)


def update_settings(conn: Connection, user: UserContext, payload: SettingsUpdateIn):
    require_role(user, {"ORG_ADMIN"})
    for key, value in payload.model_dump().items():
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_by, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_by = excluded.updated_by, updated_at = CURRENT_TIMESTAMP
            """,
            (key, json.dumps(value), user.id),
        )
    audit(conn, user, "UPDATE_SETTINGS", "app_settings", None, payload.model_dump())
    return settings_payload(conn)


def audit_log_view(conn: Connection, user: UserContext):
    require_role(user, {"ORG_ADMIN"})
    rows = conn.execute(
        """
        SELECT al.id, u.email AS actor, al.action, al.entity_type, al.entity_id, al.details, al.created_at
        FROM audit_logs al
        JOIN users u ON u.id = al.actor_user_id
        ORDER BY al.id DESC
        LIMIT 200
        """
    ).fetchall()
    return rows_to_dicts(rows)


def csv_response(filename: str, rows: list[dict]):
    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("empty\n")
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def export_report(conn: Connection, user: UserContext, report_name: str):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER"})
    if report_name == "inventory":
        return csv_response("inventory.csv", inventory_view(conn, user))
    if report_name == "orders":
        return csv_response("orders.csv", list_orders(conn, user))
    if report_name == "receiving":
        return csv_response("receiving.csv", list_receipts(conn, user))
    if report_name == "movements":
        return csv_response("inventory_movements.csv", movement_view(conn, user))
    raise HTTPException(status_code=404, detail="Unknown report")


