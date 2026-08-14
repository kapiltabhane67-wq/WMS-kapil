"use client";

import { ClipboardCheck, PackageCheck, ScanBarcode } from "lucide-react";
import { FormEvent, useState } from "react";

import { FormPanel, Input, NumberInput, Select } from "../../components/forms";
import { SimpleTable } from "../../components/simple-table";
import type { InventoryRow, ReceiptRow, ReferenceData, SubmitJson } from "../../lib/types";
import { InventoryView } from "./inventory-view";

export function ReceivingView({
  reference,
  submitJson,
  inventory,
  receipts,
}: {
  reference: ReferenceData | null;
  submitJson: SubmitJson;
  inventory: InventoryRow[];
  receipts: ReceiptRow[];
}) {
  const sellerOptions = reference?.sellers.map((item) => item.code) ?? [];
  const warehouseOptions = reference?.warehouses.map((item) => item.code) ?? [];
  const [sellerCode, setSellerCode] = useState("");
  const [warehouseCode, setWarehouseCode] = useState("");
  const [sku, setSku] = useState("");
  const [scanValue, setScanValue] = useState("");
  const [binCode, setBinCode] = useState("");
  const [receiptRef, setReceiptRef] = useState("");
  const [goodQty, setGoodQty] = useState(1);
  const [damagedQty, setDamagedQty] = useState(0);
  const productsForSeller = reference?.products.filter((item) => !sellerCode || item.seller_code === sellerCode) ?? [];
  const productOptions = productsForSeller.map((item) => item.sku);
  const selectedProduct = productsForSeller.find((item) => item.sku === sku);
  const binsForWarehouse = reference?.bins.filter((item) => item.warehouse_code === warehouseCode).map((item) => item.code) ?? [];
  const canReceive = Boolean(sellerCode && warehouseCode && sku && binCode && receiptRef && goodQty + damagedQty > 0);

  function resolveScan() {
    const normalized = scanValue.trim().toUpperCase();
    if (!normalized) return;
    const match = productsForSeller.find((item) => item.sku.toUpperCase() === normalized || item.upc.toUpperCase() === normalized);
    if (match) {
      setSku(match.sku);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!canReceive) return;
    submitJson(
      "/v1/receiving/complete",
      {
        seller_code: sellerCode,
        warehouse_code: warehouseCode,
        receipt_ref: receiptRef,
        items: [{ sku, bin_code: binCode, good_qty: goodQty, damaged_qty: damagedQty }],
      },
      "Receipt completed and inventory ledger updated"
    );
  }

  return (
    <div className="grid">
      <div className="grid forms">
        <FormPanel title="Receive Stock" icon={<PackageCheck size={18} />} onSubmit={submit}>
          <div className="receiver-flow">
            <span>1. Receipt ref</span>
            <span>2. Seller + warehouse</span>
            <span>3. Scan SKU/UPC</span>
            <span>4. Bin + qty</span>
            <span>5. Confirm</span>
          </div>
          <Input label="Receipt reference (ASN, tracking number, or drop-off ticket)" value={receiptRef} onChange={setReceiptRef} />
          <Select label="Seller" value={sellerCode} onChange={setSellerCode} options={sellerOptions} placeholder="Create a seller first" />
          <Select label="Warehouse" value={warehouseCode} onChange={setWarehouseCode} options={warehouseOptions} placeholder="Create a warehouse first" />
          <div className="row">
            <Input label="Scan / type SKU or UPC barcode" value={scanValue} onChange={setScanValue} />
            <button type="button" onClick={resolveScan} disabled={!sellerCode || !scanValue.trim()}>
              <ScanBarcode size={16} />
              Resolve Scan
            </button>
          </div>
          <Select label="SKU - Stock Keeping Unit (product code)" value={sku} onChange={setSku} options={productOptions} placeholder="Create/select seller product first" />
          {selectedProduct && <div className="notice">Resolved product: {selectedProduct.name} | UPC/barcode: {selectedProduct.upc}</div>}
          <Select label="Bin (storage location)" value={binCode} onChange={setBinCode} options={binsForWarehouse} placeholder="Create/select warehouse bin first" />
          <div className="row">
            <NumberInput label="Good qty" value={goodQty} onChange={setGoodQty} />
            <NumberInput label="Damaged qty" value={damagedQty} onChange={setDamagedQty} />
          </div>
          {!canReceive && <div className="notice">Receiver must enter receipt ref, seller, warehouse, SKU/UPC, bin, and at least one good/damaged unit.</div>}
          <button className="primary" type="submit" disabled={!canReceive}>
            <ClipboardCheck size={16} />
            Complete Receipt
          </button>
        </FormPanel>
        <InventoryView inventory={inventory} compact />
      </div>
      <SimpleTable title="Receiving History" rows={receipts} columns={["id", "receipt_ref", "seller_code", "warehouse_code", "good_qty", "damaged_qty", "status", "created_by"]} />
    </div>
  );
}
