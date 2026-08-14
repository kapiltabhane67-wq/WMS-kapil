"use client";

import { SlidersHorizontal } from "lucide-react";
import { FormEvent, useState } from "react";

import { FormPanel, Input, NumberInput, Select } from "../../components/forms";
import { SimpleTable } from "../../components/simple-table";
import type { InventoryRow, ReferenceData, SubmitJson } from "../../lib/types";

export function InventoryView({
  inventory,
  compact = false,
  reference,
  submitJson,
  canAdjust = false,
}: {
  inventory: InventoryRow[];
  compact?: boolean;
  reference?: ReferenceData | null;
  submitJson?: SubmitJson;
  canAdjust?: boolean;
}) {
  const [sellerCode, setSellerCode] = useState("");
  const [warehouseCode, setWarehouseCode] = useState("");
  const [sku, setSku] = useState("");
  const [binCode, setBinCode] = useState("");
  const [quantityDelta, setQuantityDelta] = useState(0);
  const [reason, setReason] = useState("");

  function submitAdjustment(event: FormEvent) {
    event.preventDefault();
    if (!submitJson || !sellerCode || !warehouseCode || !sku || !binCode || quantityDelta === 0 || !reason.trim()) return;
    submitJson(
      "/v1/inventory/adjustments",
      {
        seller_code: sellerCode,
        warehouse_code: warehouseCode,
        sku,
        bin_code: binCode,
        quantity_delta: quantityDelta,
        reason,
      },
      "Inventory adjustment recorded in ledger"
    );
    setReason("");
    setQuantityDelta(0);
  }

  const availableBins = reference?.bins.filter((bin) => !warehouseCode || bin.warehouse_code === warehouseCode).map((bin) => bin.code) ?? [];

  return (
    <div className="grid forms">
      {canAdjust && reference && submitJson && !compact && (
        <FormPanel title="Manager Stock Adjustment" icon={<SlidersHorizontal size={18} />} onSubmit={submitAdjustment}>
          <div className="notice">
            Use this only for approved corrections such as damage, cycle count difference, lost stock, or found stock. It creates a ledger movement.
          </div>
          <Select label="Seller" value={sellerCode} onChange={setSellerCode} options={reference.sellers.map((item) => item.code)} placeholder="Create seller first" />
          <Select label="Warehouse" value={warehouseCode} onChange={setWarehouseCode} options={reference.warehouses.map((item) => item.code)} placeholder="Create warehouse first" />
          <Select label="SKU - Stock Keeping Unit (product code)" value={sku} onChange={setSku} options={reference.products.map((item) => item.sku)} placeholder="Create product first" />
          <Select label="Bin (storage location)" value={binCode} onChange={setBinCode} options={availableBins} placeholder="Create bin first" />
          <NumberInput label="Quantity change (+ add / - reduce)" value={quantityDelta} onChange={setQuantityDelta} min={-999999} />
          <Input label="Reason required" value={reason} onChange={setReason} />
          <button className="primary" type="submit" disabled={!sellerCode || !warehouseCode || !sku || !binCode || quantityDelta === 0 || !reason.trim()}>
            <SlidersHorizontal size={16} />
            Record Adjustment
          </button>
        </FormPanel>
      )}
      <SimpleTable
        title={compact ? "Current Inventory" : "Inventory"}
        rows={inventory}
        columns={["seller_code", "sku", "warehouse_code", "bin_code", "good_qty", "reserved_qty", "available_qty", "damaged_qty"]}
      />
    </div>
  );
}
