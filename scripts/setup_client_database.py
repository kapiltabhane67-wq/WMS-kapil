import json
import os
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
DATABASE_PATH = BACKEND_DIR / "data" / "wms_client_ready.sqlite3"


def main():
    sys.path.insert(0, str(BACKEND_DIR))
    os.environ["DATABASE_PATH"] = str(DATABASE_PATH)
    from core.database.connection import init_db
    from core.database.seed import seed_if_empty

    init_db()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        seed_if_empty(conn)
        conn.commit()
        counts = {}
        for table in ["sellers", "warehouses", "bins", "products", "users", "sales_orders", "inventory_balances"]:
            counts[table] = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
        print(json.dumps({"database": str(DATABASE_PATH), "counts": counts}, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
