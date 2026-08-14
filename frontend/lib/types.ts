export type User = {
  email: string;
  full_name: string;
  role: string;
};

export type Dashboard = {
  available_units: number;
  physical_good_units: number;
  reserved_units: number;
  open_orders: number;
  ready_pick_tasks: number;
};

export type ManagerConsole = {
  low_stock_threshold: number;
  warehouse_codes: string[];
  counts: {
    open_orders: number;
    awaiting_stock_orders: number;
    active_pick_tasks: number;
    low_stock_rows: number;
    damaged_stock_rows: number;
    recent_receipts: number;
  };
  low_stock: InventoryRow[];
  damaged_stock: InventoryRow[];
  open_orders: OrderRow[];
  active_pick_tasks: PickTask[];
  recent_receipts: ReceiptRow[];
  recent_adjustments: MovementRow[];
};

export type InventoryRow = {
  seller_code: string;
  sku: string;
  product_name: string;
  warehouse_code: string;
  bin_code: string;
  good_qty: number;
  damaged_qty: number;
  reserved_qty: number;
  available_qty: number;
};

export type OrderRow = {
  id: number;
  seller_code: string;
  warehouse_code: string | null;
  marketplace: string;
  external_order_id: string;
  status: string;
  ship_to_name: string;
  ship_to_city: string;
  carrier: string | null;
  tracking_number: string | null;
  shipment_status: string | null;
};

export type PickTask = {
  id: number;
  order_id: number;
  status: string;
  warehouse_code: string;
  assigned_to: string | null;
  external_order_id: string;
  ship_to_name: string;
  ship_to_city: string;
  pick_items: string;
  first_sku: string | null;
  first_bin_code: string | null;
  total_units: number;
  shipment_id: number | null;
  carrier: string | null;
  tracking_number: string | null;
  shipment_status: string | null;
};

export type DocumentRow = {
  id: number;
  document_type: string;
  reference_type: string;
  reference_id: number;
  file_name: string;
  status: string;
};

export type MovementRow = {
  id: number;
  movement_type: string;
  seller_code: string;
  sku: string;
  warehouse_code: string;
  bin_code: string;
  quantity: number;
  physical_delta: number;
  reserved_delta: number;
  reason: string;
  actor: string;
};

export type ReceiptRow = {
  id: number;
  seller_code: string;
  warehouse_code: string;
  receipt_ref: string;
  status: string;
  created_by: string;
  completed_at: string | null;
  good_qty: number;
  damaged_qty: number;
};

export type ReferenceData = {
  sellers: { id: number; code: string; name: string }[];
  warehouses: { id: number; code: string; name: string; city: string; state: string }[];
  products: { id: number; seller_code: string; sku: string; upc: string; name: string; category: string }[];
  bins: { id: number; warehouse_code: string; code: string; zone: string; rack: string; shelf: string }[];
  users: { id: number; email: string; full_name: string; role: string; active: number; seller_code: string | null; warehouse_codes: string | null }[];
};

export type AuditLogRow = {
  id: number;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: number | null;
  details: string;
  created_at: string;
};

export type AdminSettings = {
  organization_name: string;
  default_carrier: string;
  low_stock_threshold: number;
  marketplace_provider: string;
  marketplace_status: string;
  carrier_provider: string;
  carrier_status: string;
  ai_document_extraction: boolean;
  ai_voice_commands: boolean;
  ai_rag_assistant: boolean;
  policy_require_receipt_reference: boolean;
  policy_require_pick_scan: boolean;
};

export type View = "dashboard" | "setup" | "manager" | "seller" | "receiving" | "orders" | "fulfillment" | "inventory" | "documents" | "audit";

export type SubmitJson = <T = unknown>(path: string, payload: object, success: string) => Promise<T | null>;

export type AppData = {
  me: User | null;
  dashboard: Dashboard | null;
  managerConsole: ManagerConsole | null;
  inventory: InventoryRow[];
  orders: OrderRow[];
  tasks: PickTask[];
  documents: DocumentRow[];
  movements: MovementRow[];
  receipts: ReceiptRow[];
  auditLogs: AuditLogRow[];
  settings: AdminSettings | null;
  reference: ReferenceData | null;
};
