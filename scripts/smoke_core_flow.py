import json
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("WMS_BASE_URL", "http://127.0.0.1:8016")
ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@whitfieldwms.com")
ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "ChangeMe123!")


def request(method, path, payload=None, token=None):
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {body}") from exc


def request_text(method, path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE_URL + path, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8")


def login(email, password):
    result = request("POST", "/v1/auth/login", {"email": email, "password": password})
    return result["access_token"]


def expect_http_error(method, path, expected_status, payload=None, token=None):
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as exc:
        if exc.code == expected_status:
            return
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"Expected {expected_status}, got {exc.code}: {body}") from exc
    raise RuntimeError(f"Expected {expected_status}, but request succeeded: {method} {path}")


def find_qty(inventory, sku, warehouse_code, bin_code):
    for row in inventory:
        if row["sku"] == sku and row["warehouse_code"] == warehouse_code and row["bin_code"] == bin_code:
            return row
    raise AssertionError(f"Inventory row not found for {sku} {warehouse_code} {bin_code}")


def main():
    health = request("GET", "/health")
    assert health["status"] == "ok"

    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    run_id = str(int(time.time()))
    code = run_id[-6:]
    seller_code = f"SELLER-{code}"
    other_seller_code = f"OTHER-{code}"
    warehouse_code = f"WH-{code}"
    other_warehouse_code = f"WH2-{code}"
    sku = f"SKU-{code}"
    other_sku = f"OSKU-{code}"
    bin_code = "A-01"
    other_bin_code = "B-01"
    password = f"FlowPass{code}!"

    seller_created = request("POST", "/v1/admin/sellers", {"code": seller_code, "name": f"Seller {code}"}, token=admin_token)
    other_seller_created = request("POST", "/v1/admin/sellers", {"code": other_seller_code, "name": f"Other Seller {code}"}, token=admin_token)
    warehouse_created = request(
        "POST",
        "/v1/admin/warehouses",
        {"code": warehouse_code, "name": f"Warehouse {code}", "city": "Reno", "state": "NV"},
        token=admin_token,
    )
    other_warehouse_created = request(
        "POST",
        "/v1/admin/warehouses",
        {"code": other_warehouse_code, "name": f"Other Warehouse {code}", "city": "Columbus", "state": "OH"},
        token=admin_token,
    )
    bin_created = request(
        "POST",
        "/v1/admin/bins",
        {"warehouse_code": warehouse_code, "code": bin_code, "zone": "A", "rack": "R1", "shelf": "S1"},
        token=admin_token,
    )
    request(
        "POST",
        "/v1/admin/bins",
        {"warehouse_code": other_warehouse_code, "code": other_bin_code, "zone": "B", "rack": "R1", "shelf": "S1"},
        token=admin_token,
    )
    product_created = request(
        "POST",
        "/v1/admin/products",
        {"seller_code": seller_code, "sku": sku, "upc": f"UPC-{code}", "name": "Flow Product", "category": "General"},
        token=admin_token,
    )
    request(
        "POST",
        "/v1/admin/products",
        {"seller_code": other_seller_code, "sku": other_sku, "upc": f"OUPC-{code}", "name": "Other Product", "category": "General"},
        token=admin_token,
    )
    request("PATCH", f"/v1/admin/sellers/{seller_created['id']}", {"name": f"Seller Updated {code}"}, token=admin_token)
    request(
        "PATCH",
        f"/v1/admin/warehouses/{warehouse_created['id']}",
        {"name": f"Warehouse Updated {code}", "city": "Reno", "state": "NV"},
        token=admin_token,
    )
    request("PATCH", f"/v1/admin/bins/{bin_created['id']}", {"zone": "B", "rack": "R2", "shelf": "S2"}, token=admin_token)
    request("PATCH", f"/v1/admin/products/{product_created['id']}", {"name": "Flow Product Updated", "category": "General", "upc": f"UPC-{code}"}, token=admin_token)

    receiver_email = f"receiver-{code}@whitfieldwms.com"
    manager_email = f"manager-{code}@whitfieldwms.com"
    picker_email = f"picker-{code}@whitfieldwms.com"
    seller_email = f"seller-{code}@client.example.com"
    receiver_created = request(
        "POST",
        "/v1/admin/users",
        {"email": receiver_email, "full_name": "Flow Receiver", "role": "RECEIVER", "password": password, "warehouse_codes": [warehouse_code]},
        token=admin_token,
    )
    manager_created = request(
        "POST",
        "/v1/admin/users",
        {"email": manager_email, "full_name": "Flow Manager", "role": "WAREHOUSE_MANAGER", "password": password, "warehouse_codes": [warehouse_code]},
        token=admin_token,
    )
    picker_created = request(
        "POST",
        "/v1/admin/users",
        {"email": picker_email, "full_name": "Flow Picker", "role": "PICKER_PACKER", "password": password, "warehouse_codes": [warehouse_code]},
        token=admin_token,
    )
    seller_user_created = request(
        "POST",
        "/v1/admin/users",
        {"email": seller_email, "full_name": "Seller Viewer", "role": "SELLER_VIEWER", "password": password, "seller_code": seller_code},
        token=admin_token,
    )
    request(
        "PATCH",
        f"/v1/admin/users/{receiver_created['id']}",
        {"full_name": "Flow Receiver Updated", "role": "RECEIVER", "warehouse_codes": [warehouse_code]},
        token=admin_token,
    )
    request("POST", f"/v1/admin/users/{seller_user_created['id']}/active", {"active": False}, token=admin_token)
    expect_http_error("POST", "/v1/auth/login", 401, {"email": seller_email, "password": password})
    request("POST", f"/v1/admin/users/{seller_user_created['id']}/active", {"active": True}, token=admin_token)
    request("POST", f"/v1/admin/users/{picker_created['id']}/reset-password", {"password": password}, token=admin_token)
    settings = request(
        "PUT",
        "/v1/admin/settings",
        {
            "organization_name": "Flow Org",
            "default_carrier": "UPS",
            "low_stock_threshold": 5,
            "marketplace_provider": "Shopify",
            "marketplace_status": "CONFIGURED_PENDING_KEYS",
            "carrier_provider": "Shippo",
            "carrier_status": "CONFIGURED_PENDING_KEYS",
            "ai_document_extraction": False,
            "ai_voice_commands": False,
            "ai_rag_assistant": False,
            "policy_require_receipt_reference": True,
            "policy_require_pick_scan": True,
        },
        token=admin_token,
    )
    assert settings["organization_name"] == "Flow Org"
    audit_rows = request("GET", "/v1/admin/audit-logs", token=admin_token)
    assert any(row["action"] == "UPDATE_SETTINGS" for row in audit_rows)
    report_csv = request_text("GET", "/v1/admin/reports/inventory.csv", token=admin_token)
    assert "empty" in report_csv or "seller_code" in report_csv

    receiver_token = login(receiver_email, password)
    manager_token = login(manager_email, password)
    picker_token = login(picker_email, password)
    seller_token = login(seller_email, password)

    manager_reference = request("GET", "/v1/reference", token=manager_token)
    assert [warehouse["code"] for warehouse in manager_reference["warehouses"]] == [warehouse_code]
    assert all(bin_row["warehouse_code"] == warehouse_code for bin_row in manager_reference["bins"])
    expect_http_error(
        "POST",
        "/v1/admin/products",
        403,
        {"seller_code": seller_code, "sku": f"MANAGER-{code}", "upc": f"MUPC-{code}", "name": "Manager Product", "category": "General"},
        token=manager_token,
    )
    expect_http_error("GET", "/v1/admin/audit-logs", 403, token=manager_token)
    expect_http_error(
        "POST",
        "/v1/admin/users",
        403,
        {"email": f"bad-{code}@example.com", "full_name": "Bad", "role": "RECEIVER", "password": password, "warehouse_codes": [warehouse_code]},
        token=manager_token,
    )

    expect_http_error(
        "POST",
        "/v1/inventory/adjustments",
        403,
        {"seller_code": seller_code, "warehouse_code": warehouse_code, "sku": sku, "bin_code": bin_code, "quantity_delta": 1, "reason": "Seller should not adjust stock"},
        token=seller_token,
    )

    receipt = request(
        "POST",
        "/v1/receiving/complete",
        {
            "seller_code": seller_code,
            "warehouse_code": warehouse_code,
            "receipt_ref": f"RECEIPT-{code}",
            "items": [{"sku": sku, "bin_code": bin_code, "good_qty": 10, "damaged_qty": 1}],
        },
        token=receiver_token,
    )
    assert receipt["status"] == "COMPLETED"
    duplicate_receipt = request(
        "POST",
        "/v1/receiving/complete",
        {
            "seller_code": seller_code,
            "warehouse_code": warehouse_code,
            "receipt_ref": f"RECEIPT-{code}",
            "items": [{"sku": sku, "bin_code": bin_code, "good_qty": 10, "damaged_qty": 1}],
        },
        token=receiver_token,
    )
    assert duplicate_receipt["idempotent"] is True
    expect_http_error(
        "POST",
        "/v1/receiving/complete",
        409,
        {
            "seller_code": seller_code,
            "warehouse_code": warehouse_code,
            "receipt_ref": f"RECEIPT-{code}",
            "items": [{"sku": sku, "bin_code": bin_code, "good_qty": 11, "damaged_qty": 1}],
        },
        token=receiver_token,
    )
    second_receipt = request(
        "POST",
        "/v1/receiving/complete",
        {
            "seller_code": seller_code,
            "warehouse_code": warehouse_code,
            "receipt_ref": f"RECEIPT-UPC-{code}",
            "items": [{"sku": sku, "bin_code": bin_code, "good_qty": 1, "damaged_qty": 0}],
        },
        token=receiver_token,
    )
    assert second_receipt["status"] == "COMPLETED"
    other_receipt = request(
        "POST",
        "/v1/receiving/complete",
        {
            "seller_code": other_seller_code,
            "warehouse_code": warehouse_code,
            "receipt_ref": f"OTHER-RECEIPT-{code}",
            "items": [{"sku": other_sku, "bin_code": bin_code, "good_qty": 5, "damaged_qty": 0}],
        },
        token=receiver_token,
    )
    assert other_receipt["status"] == "COMPLETED"
    receipts = request("GET", "/v1/receiving/receipts", token=receiver_token)
    assert any(row["receipt_ref"] == f"RECEIPT-{code}" for row in receipts)
    assert any(row["receipt_ref"] == f"RECEIPT-UPC-{code}" for row in receipts)
    receiver_documents = request("GET", "/v1/documents", token=receiver_token)
    assert any(row["document_type"] == "RECEIPT" for row in receiver_documents)
    expect_http_error(
        "POST",
        "/v1/orders/import",
        403,
        {
            "seller_code": seller_code,
            "marketplace": "shopify",
            "external_order_id": f"RECEIVER-ORDER-{code}",
            "preferred_warehouse_code": warehouse_code,
            "ship_to_name": "Receiver Customer",
            "ship_to_city": "Austin",
            "items": [{"sku": sku, "quantity": 1}],
        },
        token=receiver_token,
    )
    expect_http_error("GET", "/v1/fulfillment/pick-tasks", 403, token=receiver_token)
    expect_http_error(
        "POST",
        "/v1/inventory/adjustments",
        403,
        {"seller_code": seller_code, "warehouse_code": warehouse_code, "sku": sku, "bin_code": bin_code, "quantity_delta": 1, "reason": "Receiver cannot adjust"},
        token=receiver_token,
    )

    before = find_qty(request("GET", f"/v1/inventory?seller_code={seller_code}", token=admin_token), sku, warehouse_code, bin_code)
    assert before["good_qty"] == 11
    manager_adjust = request(
        "POST",
        "/v1/inventory/adjustments",
        {"seller_code": seller_code, "warehouse_code": warehouse_code, "sku": sku, "bin_code": bin_code, "quantity_delta": 1, "reason": "Cycle count found one extra unit"},
        token=manager_token,
    )
    assert manager_adjust["status"] == "ADJUSTED"
    after_adjust = find_qty(request("GET", f"/v1/inventory?seller_code={seller_code}", token=manager_token), sku, warehouse_code, bin_code)
    assert after_adjust["good_qty"] == 12

    order = request(
        "POST",
        "/v1/orders/import",
        {
            "seller_code": seller_code,
            "marketplace": "shopify",
            "external_order_id": f"ORDER-{code}",
            "preferred_warehouse_code": warehouse_code,
            "ship_to_name": "Test Customer",
            "ship_to_city": "Austin",
            "items": [{"sku": sku, "quantity": 2}],
        },
        token=manager_token,
    )
    assert order["status"] == "RESERVED"
    other_order = request(
        "POST",
        "/v1/orders/import",
        {
            "seller_code": other_seller_code,
            "marketplace": "shopify",
            "external_order_id": f"OTHER-ORDER-{code}",
            "preferred_warehouse_code": warehouse_code,
            "ship_to_name": "Other Seller Customer",
            "ship_to_city": "Austin",
            "items": [{"sku": other_sku, "quantity": 1}],
        },
        token=manager_token,
    )
    assert other_order["status"] == "RESERVED"
    expect_http_error(
        "POST",
        "/v1/orders/import",
        403,
        {
            "seller_code": other_seller_code,
            "marketplace": "shopify",
            "external_order_id": f"BLOCKED-ORDER-{code}",
            "preferred_warehouse_code": other_warehouse_code,
            "ship_to_name": "Other Customer",
            "ship_to_city": "Columbus",
            "items": [{"sku": other_sku, "quantity": 1}],
        },
        token=manager_token,
    )

    duplicate = request(
        "POST",
        "/v1/orders/import",
        {
            "seller_code": seller_code,
            "marketplace": "shopify",
            "external_order_id": f"ORDER-{code}",
            "preferred_warehouse_code": warehouse_code,
            "ship_to_name": "Test Customer",
            "ship_to_city": "Austin",
            "items": [{"sku": sku, "quantity": 2}],
        },
        token=manager_token,
    )
    assert duplicate["idempotent"] is True

    after_reserve = find_qty(request("GET", f"/v1/inventory?seller_code={seller_code}", token=admin_token), sku, warehouse_code, bin_code)
    assert after_reserve["good_qty"] == 12
    assert after_reserve["reserved_qty"] == 2

    order_detail = request("GET", f"/v1/orders/{order['order_id']}", token=manager_token)
    task_id = order_detail["pick_tasks"][0]["id"]
    pick_tasks = request("GET", "/v1/fulfillment/pick-tasks", token=picker_token)
    matching_task = next(task for task in pick_tasks if task["id"] == task_id)
    assert matching_task["first_sku"] == sku
    assert matching_task["first_bin_code"] == bin_code
    assert matching_task["total_units"] == 2
    manager_console = request("GET", "/v1/manager/console", token=manager_token)
    assert manager_console["counts"]["active_pick_tasks"] >= 1
    assert warehouse_code in manager_console["warehouse_codes"]
    expect_http_error(
        "POST",
        f"/v1/fulfillment/pick-tasks/{task_id}/pack",
        409,
        {"carrier": "UPS", "weight_oz": 16, "length_in": 10, "width_in": 8, "height_in": 4},
        token=picker_token,
    )
    expect_http_error("POST", f"/v1/fulfillment/pick-tasks/{task_id}/scan", 404, {"sku": other_sku, "bin_code": bin_code, "quantity": 1}, token=picker_token)
    expect_http_error(
        "POST",
        "/v1/receiving/complete",
        403,
        {
            "seller_code": seller_code,
            "warehouse_code": warehouse_code,
            "receipt_ref": f"PICKER-BLOCKED-{code}",
            "items": [{"sku": sku, "bin_code": bin_code, "good_qty": 1, "damaged_qty": 0}],
        },
        token=picker_token,
    )
    expect_http_error(
        "POST",
        "/v1/inventory/adjustments",
        403,
        {"seller_code": seller_code, "warehouse_code": warehouse_code, "sku": sku, "bin_code": bin_code, "quantity_delta": 1, "reason": "Picker cannot adjust"},
        token=picker_token,
    )
    expect_http_error("GET", "/v1/admin/audit-logs", 403, token=picker_token)

    picked = request("POST", f"/v1/fulfillment/pick-tasks/{task_id}/scan", {"sku": sku, "bin_code": bin_code, "quantity": 2}, token=picker_token)
    assert picked["status"] == "PICKED"
    expect_http_error("POST", f"/v1/fulfillment/pick-tasks/{task_id}/scan", 409, {"sku": sku, "bin_code": bin_code, "quantity": 1}, token=picker_token)

    packed = request(
        "POST",
        f"/v1/fulfillment/pick-tasks/{task_id}/pack",
        {"carrier": "UPS", "weight_oz": 16, "length_in": 10, "width_in": 8, "height_in": 4},
        token=picker_token,
    )
    assert packed["status"] == "LABEL_CREATED"
    duplicate_pack = request(
        "POST",
        f"/v1/fulfillment/pick-tasks/{task_id}/pack",
        {"carrier": "UPS", "weight_oz": 16, "length_in": 10, "width_in": 8, "height_in": 4},
        token=picker_token,
    )
    assert duplicate_pack["idempotent"] is True
    assert duplicate_pack["shipment_id"] == packed["shipment_id"]
    packed_tasks = request("GET", "/v1/fulfillment/pick-tasks", token=picker_token)
    packed_task = next(task for task in packed_tasks if task["id"] == task_id)
    assert packed_task["shipment_id"] == packed["shipment_id"]
    assert packed_task["tracking_number"] == packed["tracking_number"]
    assert packed_task["shipment_status"] == "LABEL_CREATED"
    documents_for_seller = request("GET", "/v1/documents", token=seller_token)
    assert any(row["document_type"] == "INVOICE" for row in documents_for_seller)
    assert any(row["document_type"] == "SHIPPING_LABEL" for row in documents_for_seller)

    dispatched = request("POST", f"/v1/shipments/{packed['shipment_id']}/dispatch", token=picker_token)
    assert dispatched["status"] == "SHIPPED"
    duplicate_dispatch = request("POST", f"/v1/shipments/{packed['shipment_id']}/dispatch", token=picker_token)
    assert duplicate_dispatch["idempotent"] is True

    after_ship = find_qty(request("GET", f"/v1/inventory?seller_code={seller_code}", token=admin_token), sku, warehouse_code, bin_code)
    assert after_ship["good_qty"] == 10
    assert after_ship["reserved_qty"] == 0

    final_order = request("GET", f"/v1/orders/{order['order_id']}", token=seller_token)
    assert final_order["status"] == "SHIPPED"
    seller_orders = request("GET", "/v1/orders", token=seller_token)
    assert any(row["tracking_number"] == packed["tracking_number"] for row in seller_orders)
    assert all(row["seller_code"] == seller_code for row in seller_orders)
    assert all(row["id"] != other_order["order_id"] for row in seller_orders)
    expect_http_error("GET", f"/v1/orders/{other_order['order_id']}", 403, token=seller_token)
    seller_inventory = request("GET", "/v1/inventory", token=seller_token)
    assert seller_inventory
    assert all(row["seller_code"] == seller_code for row in seller_inventory)
    assert all(row["sku"] != other_sku for row in seller_inventory)
    seller_movements = request("GET", "/v1/inventory/movements", token=seller_token)
    assert seller_movements
    assert all(row["seller_code"] == seller_code for row in seller_movements)
    seller_reference = request("GET", "/v1/reference", token=seller_token)
    assert [row["code"] for row in seller_reference["sellers"]] == [seller_code]
    assert all(row["seller_code"] == seller_code for row in seller_reference["products"])
    assert all(row["sku"] != other_sku for row in seller_reference["products"])
    assert all(row["warehouse_code"] == warehouse_code for row in seller_reference["bins"])
    documents_for_seller = request("GET", "/v1/documents", token=seller_token)
    assert any(row["document_type"] == "RECEIPT" for row in documents_for_seller)
    assert any(row["document_type"] == "INVOICE" for row in documents_for_seller)
    assert any(row["document_type"] == "SHIPPING_LABEL" for row in documents_for_seller)
    assert all(row["reference_id"] != other_receipt["receipt_id"] for row in documents_for_seller if row["reference_type"] == "inbound_receipt")
    expect_http_error(
        "POST",
        "/v1/inventory/adjustments",
        403,
        {"seller_code": seller_code, "warehouse_code": warehouse_code, "sku": sku, "bin_code": bin_code, "quantity_delta": -1, "reason": "Seller blocked"},
        token=seller_token,
    )
    expect_http_error("GET", f"/v1/orders/{order['order_id']}", 403, token=receiver_token)
    print("Clean setup WMS flow passed")
    print(json.dumps({
        "seller_code": seller_code,
        "warehouse_code": warehouse_code,
        "sku": sku,
        "tracking_number": packed["tracking_number"],
        "receiver_receipts_checked": 2,
        "seller_portal_checked": True,
        "roles_checked": ["ORG_ADMIN", "WAREHOUSE_MANAGER", "RECEIVER", "PICKER_PACKER", "SELLER_VIEWER"],
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
