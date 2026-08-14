import { SimpleTable } from "../../components/simple-table";
import type { Dashboard, InventoryRow, OrderRow } from "../../lib/types";

export function DashboardView({
  dashboard,
  orders,
  inventory,
}: {
  dashboard: Dashboard | null;
  orders: OrderRow[];
  inventory: InventoryRow[];
}) {
  const stats = [
    ["Available", dashboard?.available_units ?? 0],
    ["Physical good", dashboard?.physical_good_units ?? 0],
    ["Reserved", dashboard?.reserved_units ?? 0],
    ["Open orders", dashboard?.open_orders ?? 0],
    ["Pick tasks", dashboard?.ready_pick_tasks ?? 0],
  ];
  return (
    <div className="grid">
      <div className="grid stats">
        {stats.map(([label, value]) => (
          <div className="panel stat" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="grid forms">
        <SimpleTable title="Latest Orders" rows={orders.slice(0, 6)} columns={["id", "external_order_id", "warehouse_code", "status"]} />
        <SimpleTable title="Inventory Watch" rows={inventory.slice(0, 8)} columns={["sku", "warehouse_code", "bin_code", "available_qty"]} />
      </div>
    </div>
  );
}
