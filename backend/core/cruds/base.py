from collections.abc import Sequence
from sqlite3 import Connection, Cursor, Row
from typing import Any


DbParams = Sequence[Any]


def fetch_one(conn: Connection, query: str, params: DbParams = ()) -> Row | None:
    return conn.execute(query, params).fetchone()


def fetch_all(conn: Connection, query: str, params: DbParams = ()) -> list[Row]:
    return conn.execute(query, params).fetchall()


def execute(conn: Connection, query: str, params: DbParams = ()) -> Cursor:
    return conn.execute(query, params)


def row_to_dict(row: Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None

