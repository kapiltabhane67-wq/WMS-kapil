import { SimpleTable } from "../../components/simple-table";
import type { MovementRow } from "../../lib/types";

export function LedgerView({ movements }: { movements: MovementRow[] }) {
  return <SimpleTable title="Inventory Movement Ledger" rows={movements} columns={["id", "movement_type", "sku", "warehouse_code", "bin_code", "physical_delta", "reserved_delta", "actor"]} />;
}
