import { AlertTriangle, Boxes, ClipboardList, PackageCheck, Warehouse } from "lucide-react";

import { SimpleTable } from "../../components/simple-table";
import type { ManagerConsole } from "../../lib/types";

export function ManagerView({ consoleData }: { consoleData: ManagerConsole | null }) {
  const counts = consoleData?.counts;
  const stats = [
    ["Open orders", counts?.open_orders ?? 0, <ClipboardList size={18} key="orders" />],
    ["Awaiting stock", counts?.awaiting_stock_orders ?? 0, <AlertTriangle size={18} key="awaiting" />],
    ["Active pick tasks", counts?.active_pick_tasks ?? 0, <PackageCheck size={18} key="pick" />],
    ["Low-stock rows", counts?.low_stock_rows ?? 0, <Boxes size={18} key="low" />],
    ["Damaged rows", counts?.damaged_stock_rows ?? 0, <AlertTriangle size={18} key="damage" />],
  ];

  return (
    <div className="grid">
      <div className="manager-hero panel">
        <div>
          <span className="eyebrow">Warehouse manager control center</span>
          <h2>Today’s operational risks</h2>
          <p>
            This screen is warehouse-scoped. It highlights stock shortages, damaged inventory, open fulfillment work,
            and recent receiving so the manager can act before orders get delayed.
          </p>
        </div>
        <div className="manager-scope">
          <Warehouse size={18} />
          <span>{consoleData?.warehouse_codes.length ? consoleData.warehouse_codes.join(", ") : "No assigned warehouse"}</span>
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
          title={`Low Stock ≤ ${consoleData?.low_stock_threshold ?? 0}`}
          rows={consoleData?.low_stock ?? []}
          columns={["seller_code", "sku", "warehouse_code", "bin_code", "available_qty", "reserved_qty"]}
        />
        <SimpleTable
          title="Open Orders"
          rows={consoleData?.open_orders ?? []}
          columns={["id", "seller_code", "external_order_id", "warehouse_code", "status", "tracking_number"]}
        />
      </div>

      <div className="grid forms">
        <SimpleTable
          title="Active Pick Queue"
          rows={consoleData?.active_pick_tasks ?? []}
          columns={["id", "order_id", "warehouse_code", "external_order_id", "pick_items", "status"]}
        />
        <SimpleTable
          title="Damaged Stock"
          rows={consoleData?.damaged_stock ?? []}
          columns={["seller_code", "sku", "warehouse_code", "bin_code", "damaged_qty", "good_qty"]}
        />
      </div>

      <div className="grid forms">
        <SimpleTable
          title="Recent Receiving"
          rows={consoleData?.recent_receipts ?? []}
          columns={["id", "seller_code", "warehouse_code", "receipt_ref", "good_qty", "damaged_qty", "status"]}
        />
        <SimpleTable
          title="Recent Manager Adjustments"
          rows={consoleData?.recent_adjustments ?? []}
          columns={["id", "movement_type", "seller_code", "sku", "warehouse_code", "bin_code", "quantity", "reason"]}
        />
      </div>
    </div>
  );
}
