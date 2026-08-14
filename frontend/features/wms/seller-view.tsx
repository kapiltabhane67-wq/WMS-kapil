import { Boxes, FileText, PackageCheck, Send, Truck } from "lucide-react";

import { SimpleTable } from "../../components/simple-table";
import type { Dashboard, DocumentRow, InventoryRow, MovementRow, OrderRow, ReferenceData } from "../../lib/types";

export function SellerView({
  reference,
  dashboard,
  inventory,
  orders,
  documents,
  movements,
}: {
  reference: ReferenceData | null;
  dashboard: Dashboard | null;
  inventory: InventoryRow[];
  orders: OrderRow[];
  documents: DocumentRow[];
  movements: MovementRow[];
}) {
  const seller = reference?.sellers[0];
  const shippedOrders = orders.filter((order) => order.status === "SHIPPED" || order.status === "DELIVERED").length;
  const activeOrders = orders.filter((order) => !["SHIPPED", "DELIVERED", "CANCELLED"].includes(order.status)).length;
  const warehouses = [...new Set(inventory.map((row) => row.warehouse_code))];
  const stats = [
    ["Available units", dashboard?.available_units ?? 0, <Boxes size={18} key="available" />],
    ["Reserved units", dashboard?.reserved_units ?? 0, <PackageCheck size={18} key="reserved" />],
    ["Active orders", activeOrders, <Send size={18} key="active" />],
    ["Shipped orders", shippedOrders, <Truck size={18} key="shipped" />],
    ["Documents", documents.length, <FileText size={18} key="documents" />],
  ];

  return (
    <div className="grid">
      <div className="manager-hero seller-hero panel">
        <div>
          <span className="eyebrow">Seller read-only portal</span>
          <h2>{seller ? `${seller.name} (${seller.code})` : "Seller account"}</h2>
          <p>
            Sellers can monitor their own stock, orders, receipts, invoices, labels, and tracking. They cannot change
            warehouse inventory or view another seller’s data.
          </p>
        </div>
        <div className="manager-scope">
          <Boxes size={18} />
          <span>{warehouses.length ? warehouses.join(", ") : "No stock received yet"}</span>
        </div>
      </div>

      <div className="grid stats">
        {stats.map(([label, value, icon]) => (
          <div className="panel stat" key={String(label)}>
            <div className="stat-row">
              <span>{label}</span>
              {icon}
            </div>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

      <div className="grid forms">
        <SimpleTable
          title="My Orders And Tracking"
          rows={orders}
          columns={["id", "external_order_id", "warehouse_code", "status", "carrier", "tracking_number", "shipment_status"]}
        />
        <SimpleTable
          title="My Inventory"
          rows={inventory}
          columns={["sku", "product_name", "warehouse_code", "bin_code", "good_qty", "reserved_qty", "available_qty", "damaged_qty"]}
        />
      </div>

      <div className="grid forms">
        <SimpleTable
          title="My Documents"
          rows={documents}
          columns={["id", "document_type", "reference_type", "reference_id", "file_name", "status"]}
        />
        <SimpleTable
          title="My Stock Ledger"
          rows={movements.slice(0, 20)}
          columns={["id", "movement_type", "sku", "warehouse_code", "bin_code", "quantity", "reason"]}
        />
      </div>
    </div>
  );
}
