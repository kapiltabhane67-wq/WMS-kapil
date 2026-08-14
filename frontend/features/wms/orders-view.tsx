"use client";

import { Send } from "lucide-react";
import { FormEvent, useState } from "react";

import { FormPanel, NumberInput, Select } from "../../components/forms";
import { SimpleTable } from "../../components/simple-table";
import type { OrderRow, ReferenceData, SubmitJson } from "../../lib/types";

export function OrdersView({
  submitJson,
  orders,
  reference,
  canImport = false,
}: {
  submitJson: SubmitJson;
  orders: OrderRow[];
  reference: ReferenceData | null;
  canImport?: boolean;
}) {
  const [sku, setSku] = useState("");
  const [warehouseCode, setWarehouseCode] = useState("");
  const [quantity, setQuantity] = useState(2);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!warehouseCode || !sku) return;
    const sellerCode = reference?.products.find((item) => item.sku === sku)?.seller_code;
    if (!sellerCode) return;
    submitJson(
      "/v1/orders/import",
      {
        seller_code: sellerCode,
        marketplace: "shopify",
        external_order_id: `UI-ORDER-${Date.now()}`,
        preferred_warehouse_code: warehouseCode,
        ship_to_name: "Customer",
        ship_to_city: "Austin",
        items: [{ sku, quantity }],
      },
      "Marketplace order imported, stock reserved, and pick task created"
    );
  }

  return (
    <div className="grid forms">
      {canImport && (
        <FormPanel title="Import Marketplace Order" icon={<Send size={18} />} onSubmit={submit}>
          <Select label="Warehouse" value={warehouseCode} onChange={setWarehouseCode} options={reference?.warehouses.map((item) => item.code) ?? []} placeholder="Create a warehouse first" />
          <Select label="SKU - Stock Keeping Unit (product code)" value={sku} onChange={setSku} options={reference?.products.map((item) => item.sku) ?? []} placeholder="Create a product first" />
          <NumberInput label="Quantity" value={quantity} onChange={setQuantity} />
          <button className="primary" type="submit" disabled={!warehouseCode || !sku}>
            <Send size={16} />
            Import Order
          </button>
        </FormPanel>
      )}
      <SimpleTable title="Orders" rows={orders} columns={["id", "seller_code", "external_order_id", "warehouse_code", "ship_to_city", "status", "tracking_number", "shipment_status"]} />
    </div>
  );
}
