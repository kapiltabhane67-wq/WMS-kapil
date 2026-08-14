from sqlite3 import Connection

from fastapi import HTTPException

from commons.auth import hash_password, require_role, require_warehouse_access
from core.schemas import (
    BinCreateIn, BinUpdateIn, ProductCreateIn, ProductUpdateIn, SellerCreateIn, SellerUpdateIn,
    UserActiveIn, UserContext, UserCreateIn, UserPasswordResetIn, UserUpdateIn, WarehouseCreateIn, WarehouseUpdateIn,
)
from core.services.common import audit, get_by_code, normalize_code

def create_seller(conn: Connection, user: UserContext, payload: SellerCreateIn):
    require_role(user, {"ORG_ADMIN"})
    code = normalize_code(payload.code)
    seller_id = conn.execute(
        "INSERT INTO sellers (code, name) VALUES (?, ?)",
        (code, payload.name.strip()),
    ).lastrowid
    audit(conn, user, "CREATE_SELLER", "seller", seller_id, {"code": code, "name": payload.name})
    return {"id": seller_id, "code": code, "name": payload.name.strip()}


def create_warehouse(conn: Connection, user: UserContext, payload: WarehouseCreateIn):
    require_role(user, {"ORG_ADMIN"})
    code = normalize_code(payload.code)
    warehouse_id = conn.execute(
        "INSERT INTO warehouses (code, name, city, state) VALUES (?, ?, ?, ?)",
        (code, payload.name.strip(), payload.city.strip(), payload.state.strip()),
    ).lastrowid
    audit(conn, user, "CREATE_WAREHOUSE", "warehouse", warehouse_id, payload.model_dump())
    return {"id": warehouse_id, "code": code, "name": payload.name.strip()}


def create_bin(conn: Connection, user: UserContext, payload: BinCreateIn):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER"})
    warehouse = get_by_code(conn, "warehouses", payload.warehouse_code)
    require_warehouse_access(user, warehouse["id"])
    code = normalize_code(payload.code)
    bin_id = conn.execute(
        "INSERT INTO bins (warehouse_id, code, zone, rack, shelf) VALUES (?, ?, ?, ?, ?)",
        (warehouse["id"], code, payload.zone.strip(), payload.rack.strip(), payload.shelf.strip()),
    ).lastrowid
    audit(conn, user, "CREATE_BIN", "bin", bin_id, {"warehouse_code": warehouse["code"], "code": code})
    return {"id": bin_id, "warehouse_code": warehouse["code"], "code": code}


def create_product(conn: Connection, user: UserContext, payload: ProductCreateIn):
    require_role(user, {"ORG_ADMIN"})
    seller = get_by_code(conn, "sellers", payload.seller_code)
    sku = normalize_code(payload.sku)
    product_id = conn.execute(
        """
        INSERT INTO products (seller_id, sku, upc, name, category)
        VALUES (?, ?, ?, ?, ?)
        """,
        (seller["id"], sku, payload.upc.strip(), payload.name.strip(), payload.category.strip()),
    ).lastrowid
    audit(conn, user, "CREATE_PRODUCT", "product", product_id, {"seller_code": seller["code"], "sku": sku})
    return {"id": product_id, "seller_code": seller["code"], "sku": sku, "name": payload.name.strip()}


def create_user(conn: Connection, user: UserContext, payload: UserCreateIn):
    require_role(user, {"ORG_ADMIN"})
    seller_id = None
    if payload.role == "SELLER_VIEWER":
        if not payload.seller_code:
            raise HTTPException(status_code=422, detail="Seller viewer must be assigned to a seller")
        seller_id = get_by_code(conn, "sellers", payload.seller_code)["id"]
    if payload.role in {"WAREHOUSE_MANAGER", "RECEIVER", "PICKER_PACKER"} and not payload.warehouse_codes:
        raise HTTPException(status_code=422, detail="Warehouse role must be assigned to at least one warehouse")
    user_id = conn.execute(
        """
        INSERT INTO users (email, full_name, role, seller_id, password_hash)
        VALUES (?, ?, ?, ?, ?)
        """,
        (payload.email.strip().lower(), payload.full_name.strip(), payload.role, seller_id, hash_password(payload.password)),
    ).lastrowid
    for warehouse_code in payload.warehouse_codes:
        warehouse = get_by_code(conn, "warehouses", warehouse_code)
        conn.execute(
            "INSERT INTO user_warehouses (user_id, warehouse_id) VALUES (?, ?)",
            (user_id, warehouse["id"]),
        )
    audit(conn, user, "CREATE_USER", "user", user_id, {"email": payload.email, "role": payload.role})
    return {"id": user_id, "email": payload.email.strip().lower(), "role": payload.role}


def update_seller(conn: Connection, user: UserContext, seller_id: int, payload: SellerUpdateIn):
    require_role(user, {"ORG_ADMIN"})
    cursor = conn.execute("UPDATE sellers SET name = ? WHERE id = ?", (payload.name.strip(), seller_id))
    if cursor.rowcount != 1:
        raise HTTPException(status_code=404, detail="Seller not found")
    audit(conn, user, "UPDATE_SELLER", "seller", seller_id, payload.model_dump())
    return {"id": seller_id, "status": "UPDATED"}


def update_warehouse(conn: Connection, user: UserContext, warehouse_id: int, payload: WarehouseUpdateIn):
    require_role(user, {"ORG_ADMIN"})
    cursor = conn.execute(
        "UPDATE warehouses SET name = ?, city = ?, state = ? WHERE id = ?",
        (payload.name.strip(), payload.city.strip(), payload.state.strip(), warehouse_id),
    )
    if cursor.rowcount != 1:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    audit(conn, user, "UPDATE_WAREHOUSE", "warehouse", warehouse_id, payload.model_dump())
    return {"id": warehouse_id, "status": "UPDATED"}


def update_bin(conn: Connection, user: UserContext, bin_id: int, payload: BinUpdateIn):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER"})
    bin_row = conn.execute("SELECT * FROM bins WHERE id = ?", (bin_id,)).fetchone()
    if not bin_row:
        raise HTTPException(status_code=404, detail="Bin not found")
    require_warehouse_access(user, bin_row["warehouse_id"])
    conn.execute(
        "UPDATE bins SET zone = ?, rack = ?, shelf = ? WHERE id = ?",
        (payload.zone.strip(), payload.rack.strip(), payload.shelf.strip(), bin_id),
    )
    audit(conn, user, "UPDATE_BIN", "bin", bin_id, payload.model_dump())
    return {"id": bin_id, "status": "UPDATED"}


def update_product(conn: Connection, user: UserContext, product_id: int, payload: ProductUpdateIn):
    require_role(user, {"ORG_ADMIN", "WAREHOUSE_MANAGER"})
    cursor = conn.execute(
        "UPDATE products SET name = ?, category = ?, upc = ? WHERE id = ?",
        (payload.name.strip(), payload.category.strip(), payload.upc.strip(), product_id),
    )
    if cursor.rowcount != 1:
        raise HTTPException(status_code=404, detail="Product not found")
    audit(conn, user, "UPDATE_PRODUCT", "product", product_id, payload.model_dump())
    return {"id": product_id, "status": "UPDATED"}


def update_user(conn: Connection, user: UserContext, target_user_id: int, payload: UserUpdateIn):
    require_role(user, {"ORG_ADMIN"})
    target = conn.execute("SELECT * FROM users WHERE id = ?", (target_user_id,)).fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    seller_id = None
    if payload.role == "SELLER_VIEWER":
        if not payload.seller_code:
            raise HTTPException(status_code=422, detail="Seller viewer must be assigned to a seller")
        seller_id = get_by_code(conn, "sellers", payload.seller_code)["id"]
    if payload.role in {"WAREHOUSE_MANAGER", "RECEIVER", "PICKER_PACKER"} and not payload.warehouse_codes:
        raise HTTPException(status_code=422, detail="Warehouse role must be assigned to at least one warehouse")
    conn.execute(
        "UPDATE users SET full_name = ?, role = ?, seller_id = ? WHERE id = ?",
        (payload.full_name.strip(), payload.role, seller_id, target_user_id),
    )
    conn.execute("DELETE FROM user_warehouses WHERE user_id = ?", (target_user_id,))
    for warehouse_code in payload.warehouse_codes:
        warehouse = get_by_code(conn, "warehouses", warehouse_code)
        conn.execute("INSERT INTO user_warehouses (user_id, warehouse_id) VALUES (?, ?)", (target_user_id, warehouse["id"]))
    audit(conn, user, "UPDATE_USER", "user", target_user_id, payload.model_dump())
    return {"id": target_user_id, "status": "UPDATED"}


def set_user_active(conn: Connection, user: UserContext, target_user_id: int, payload: UserActiveIn):
    require_role(user, {"ORG_ADMIN"})
    if target_user_id == user.id and not payload.active:
        raise HTTPException(status_code=409, detail="Admin cannot deactivate their own account")
    cursor = conn.execute("UPDATE users SET active = ? WHERE id = ?", (1 if payload.active else 0, target_user_id))
    if cursor.rowcount != 1:
        raise HTTPException(status_code=404, detail="User not found")
    if not payload.active:
        conn.execute("DELETE FROM auth_sessions WHERE user_id = ?", (target_user_id,))
    audit(conn, user, "SET_USER_ACTIVE", "user", target_user_id, payload.model_dump())
    return {"id": target_user_id, "active": payload.active}


def reset_user_password(conn: Connection, user: UserContext, target_user_id: int, payload: UserPasswordResetIn):
    require_role(user, {"ORG_ADMIN"})
    cursor = conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(payload.password), target_user_id),
    )
    if cursor.rowcount != 1:
        raise HTTPException(status_code=404, detail="User not found")
    conn.execute("DELETE FROM auth_sessions WHERE user_id = ?", (target_user_id,))
    audit(conn, user, "RESET_USER_PASSWORD", "user", target_user_id, {"password_reset": True})
    return {"id": target_user_id, "status": "PASSWORD_RESET"}


