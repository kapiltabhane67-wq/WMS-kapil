"use client";

import { Boxes, Download, MapPin, PackagePlus, Save, UserPlus, Users, Warehouse } from "lucide-react";
import { FormEvent, useState } from "react";

import { FormPanel, Input, Select } from "../../components/forms";
import { SimpleTable } from "../../components/simple-table";
import { API_BASE } from "../../lib/constants";
import type { AdminSettings, AuditLogRow, ReferenceData, SubmitJson } from "../../lib/types";

const roles = ["ORG_ADMIN", "WAREHOUSE_MANAGER", "RECEIVER", "PICKER_PACKER", "SELLER_VIEWER"];

export function SetupView({
  reference,
  settings,
  auditLogs,
  submitJson,
  token,
}: {
  reference: ReferenceData | null;
  settings: AdminSettings | null;
  auditLogs: AuditLogRow[];
  submitJson: SubmitJson;
  token: string;
}) {
  return (
    <div className="grid">
      <SetupChecklist reference={reference} />
      <GlossaryPanel />
      <div className="grid setup-grid">
        <SellerForm submitJson={submitJson} />
        <WarehouseForm submitJson={submitJson} />
        <BinForm reference={reference} submitJson={submitJson} />
        <ProductForm reference={reference} submitJson={submitJson} />
        <UserForm reference={reference} submitJson={submitJson} />
      </div>
      <AdminSettingsPanel settings={settings} submitJson={submitJson} />
      <ReportsPanel token={token} />
      <div className="grid forms">
        <SimpleTable title="Sellers" rows={reference?.sellers ?? []} columns={["code", "name"]} />
        <SimpleTable title="Warehouses" rows={reference?.warehouses ?? []} columns={["code", "name", "city", "state"]} />
      </div>
      <div className="grid forms">
        <SimpleTable title="Products" rows={reference?.products ?? []} columns={["seller_code", "sku", "name"]} />
        <SimpleTable title="Bins" rows={reference?.bins ?? []} columns={["warehouse_code", "code", "zone", "rack", "shelf"]} />
      </div>
      <ManagementPanel reference={reference} submitJson={submitJson} />
      <SimpleTable title="Audit Logs" rows={auditLogs} columns={["id", "actor", "action", "entity_type", "entity_id", "created_at"]} />
    </div>
  );
}

function SetupChecklist({ reference }: { reference: ReferenceData | null }) {
  const sellers = reference?.sellers.length ?? 0;
  const warehouses = reference?.warehouses.length ?? 0;
  const bins = reference?.bins.length ?? 0;
  const products = reference?.products.length ?? 0;
  const users = reference?.users.filter((user) => user.role !== "ORG_ADMIN").length ?? 0;
  const steps = [
    ["1", "Seller", sellers > 0, "Required before product"],
    ["2", "Warehouse", warehouses > 0, "Required before bin and warehouse staff"],
    ["3", "Bin", bins > 0, "Required before receiving stock"],
    ["4", "Product", products > 0, "Required before receiving/order"],
    ["5", "Role users", users > 0, "Manager, receiver, picker, seller login"],
  ];
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Setup Order</h2>
        <span className="badge">Follow left to right</span>
      </div>
      <div className="panel-body setup-steps">
        {steps.map(([number, label, done, help]) => (
          <div className={done ? "setup-step done" : "setup-step"} key={String(label)}>
            <strong>{number}. {label}</strong>
            <span>{done ? "Done" : help}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function GlossaryPanel() {
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Warehouse Terms</h2>
      </div>
      <div className="panel-body glossary">
        <div>
          <strong>SKU - Stock Keeping Unit</strong>
          <span>Internal product code. It answers: what item is this?</span>
        </div>
        <div>
          <strong>Bin</strong>
          <span>Exact storage location. It answers: where is this item kept?</span>
        </div>
        <div>
          <strong>Reservation</strong>
          <span>Stock promised to an order. Physical stock is deducted only when shipped.</span>
        </div>
      </div>
    </div>
  );
}

function SellerForm({ submitJson }: { submitJson: SubmitJson }) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const canSubmit = code.trim().length >= 2 && name.trim().length >= 1;
  return (
    <FormPanel
      title="Create Seller"
      icon={<Users size={18} />}
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        if (canSubmit) submitJson("/v1/admin/sellers", { code, name }, "Seller created");
      }}
    >
      <Input label="Seller code" value={code} onChange={setCode} />
      <Input label="Seller name" value={name} onChange={setName} />
      {!canSubmit && <div className="notice">Need Seller code minimum 2 characters and Seller name minimum 1 character.</div>}
      <button className="primary" type="submit" disabled={!canSubmit}>Create Seller</button>
    </FormPanel>
  );
}

function WarehouseForm({ submitJson }: { submitJson: SubmitJson }) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const canSubmit = code.trim().length >= 2 && name.trim().length >= 2 && city.trim().length >= 2 && state.trim().length >= 2;
  return (
    <FormPanel
      title="Create Warehouse"
      icon={<Warehouse size={18} />}
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        if (canSubmit) submitJson("/v1/admin/warehouses", { code, name, city, state }, "Warehouse created");
      }}
    >
      <Input label="Warehouse code" value={code} onChange={setCode} />
      <Input label="Warehouse name" value={name} onChange={setName} />
      <Input label="City" value={city} onChange={setCity} />
      <Input label="State" value={state} onChange={setState} />
      {!canSubmit && <div className="notice">Need warehouse code, name, city, and state. Example: RENO / Reno Warehouse / Reno / NV.</div>}
      <button className="primary" type="submit" disabled={!canSubmit}>Create Warehouse</button>
    </FormPanel>
  );
}

function BinForm({ reference, submitJson }: { reference: ReferenceData | null; submitJson: SubmitJson }) {
  const warehouseOptions = reference?.warehouses.map((item) => item.code) ?? [];
  const [warehouseCode, setWarehouseCode] = useState("");
  const [code, setCode] = useState("");
  const [zone, setZone] = useState("");
  const [rack, setRack] = useState("");
  const [shelf, setShelf] = useState("");
  const canSubmit = Boolean(warehouseCode) && code.trim().length >= 2 && zone.trim().length >= 1 && rack.trim().length >= 1 && shelf.trim().length >= 1;
  return (
    <FormPanel
      title="Create Bin"
      icon={<MapPin size={18} />}
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        if (canSubmit) submitJson("/v1/admin/bins", { warehouse_code: warehouseCode, code, zone, rack, shelf }, "Bin location created");
      }}
    >
      <Select label="Warehouse" value={warehouseCode} onChange={setWarehouseCode} options={warehouseOptions} placeholder="Create a warehouse first" />
      <Input label="Bin code (exact storage location)" value={code} onChange={setCode} />
      <Input label="Zone" value={zone} onChange={setZone} />
      <Input label="Rack" value={rack} onChange={setRack} />
      <Input label="Shelf" value={shelf} onChange={setShelf} />
      {!warehouseCode && <div className="notice">Create/select a warehouse first. A bin always belongs to one warehouse.</div>}
      {warehouseCode && !canSubmit && <div className="notice">Need bin code, zone, rack, and shelf. Example: A-01-01 / A / 01 / 01.</div>}
      <button className="primary" type="submit" disabled={!canSubmit}>Create Bin</button>
    </FormPanel>
  );
}

function ProductForm({ reference, submitJson }: { reference: ReferenceData | null; submitJson: SubmitJson }) {
  const sellerOptions = reference?.sellers.map((item) => item.code) ?? [];
  const [sellerCode, setSellerCode] = useState("");
  const [sku, setSku] = useState("");
  const [upc, setUpc] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const canSubmit = Boolean(sellerCode) && sku.trim().length >= 2 && upc.trim().length >= 4 && name.trim().length >= 1 && category.trim().length >= 1;
  return (
    <FormPanel
      title="Create Product"
      icon={<PackagePlus size={18} />}
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        if (canSubmit) submitJson("/v1/admin/products", { seller_code: sellerCode, sku, upc, name, category }, "Product created");
      }}
    >
      <Select label="Seller" value={sellerCode} onChange={setSellerCode} options={sellerOptions} placeholder="Create a seller first" />
      <Input label="SKU - Stock Keeping Unit (product code)" value={sku} onChange={setSku} />
      <Input label="UPC - Universal Product Code / barcode" value={upc} onChange={setUpc} />
      <Input label="Product name" value={name} onChange={setName} />
      <Input label="Category" value={category} onChange={setCategory} />
      {!sellerCode && <div className="notice">Product is not global. First create/select Seller, then product will be saved under that seller.</div>}
      {sellerCode && !canSubmit && <div className="notice">Need SKU minimum 2 characters, UPC/barcode minimum 4 characters, product name, and category.</div>}
      <button className="primary" type="submit" disabled={!canSubmit}>Create Product</button>
    </FormPanel>
  );
}

function UserForm({ reference, submitJson }: { reference: ReferenceData | null; submitJson: SubmitJson }) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("RECEIVER");
  const [password, setPassword] = useState("");
  const sellerOptions = reference?.sellers.map((item) => item.code) ?? [];
  const warehouseOptions = reference?.warehouses.map((item) => item.code) ?? [];
  const [sellerCode, setSellerCode] = useState("");
  const [warehouseCode, setWarehouseCode] = useState("");
  const needsSeller = role === "SELLER_VIEWER";
  const needsWarehouse = ["WAREHOUSE_MANAGER", "RECEIVER", "PICKER_PACKER"].includes(role);
  const canSubmit =
    email.trim().length > 3 &&
    fullName.trim().length >= 2 &&
    password.length >= 8 &&
    (!needsSeller || Boolean(sellerCode)) &&
    (!needsWarehouse || Boolean(warehouseCode));
  return (
    <FormPanel
      title="Create User"
      icon={<UserPlus size={18} />}
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        if (!canSubmit) return;
        submitJson(
          "/v1/admin/users",
          {
            email,
            full_name: fullName,
            role,
            password,
            seller_code: needsSeller ? sellerCode : null,
            warehouse_codes: needsWarehouse ? [warehouseCode] : [],
          },
          "User created"
        );
      }}
    >
      <Input label="Email" value={email} onChange={setEmail} />
      <Input label="Full name" value={fullName} onChange={setFullName} />
      <Select label="Role" value={role} onChange={setRole} options={roles} />
      {needsSeller && <Select label="Seller access" value={sellerCode} onChange={setSellerCode} options={sellerOptions} placeholder="Create a seller first" />}
      {needsWarehouse && (
        <Select label="Warehouse access" value={warehouseCode} onChange={setWarehouseCode} options={warehouseOptions} placeholder="Create a warehouse first" />
      )}
      <Input label="Temporary password" value={password} onChange={setPassword} />
      {!canSubmit && (
        <div className="notice">
          Need email, full name, and password minimum 8 characters.
          {needsWarehouse ? " Manager/receiver/picker also needs warehouse access." : ""}
          {needsSeller ? " Seller viewer also needs seller access." : ""}
        </div>
      )}
      <button className="primary" type="submit" disabled={!canSubmit}>
        <Boxes size={16} />
        Create User
      </button>
    </FormPanel>
  );
}

function ManagementPanel({ reference, submitJson }: { reference: ReferenceData | null; submitJson: SubmitJson }) {
  const [sellerId, setSellerId] = useState("");
  const [sellerName, setSellerName] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [warehouseName, setWarehouseName] = useState("");
  const [warehouseCity, setWarehouseCity] = useState("");
  const [warehouseState, setWarehouseState] = useState("");
  const [productId, setProductId] = useState("");
  const [productName, setProductName] = useState("");
  const [productCategory, setProductCategory] = useState("");
  const [productUpc, setProductUpc] = useState("");
  const [binId, setBinId] = useState("");
  const [binZone, setBinZone] = useState("");
  const [binRack, setBinRack] = useState("");
  const [binShelf, setBinShelf] = useState("");
  const [userId, setUserId] = useState("");
  const [userFullName, setUserFullName] = useState("");
  const [userRole, setUserRole] = useState("RECEIVER");
  const [userPassword, setUserPassword] = useState("");
  const [editSellerCode, setEditSellerCode] = useState("");
  const [editWarehouseCode, setEditWarehouseCode] = useState("");

  const sellerOptions = reference?.sellers.map((item) => `${item.id} | ${item.code}`) ?? [];
  const warehouseOptions = reference?.warehouses.map((item) => `${item.id} | ${item.code}`) ?? [];
  const productOptions = reference?.products.map((item) => `${item.id} | ${item.sku}`) ?? [];
  const binOptions = reference?.bins.map((item) => `${item.id} | ${item.code}`) ?? [];
  const userOptions = reference?.users.map((item) => `${item.id} | ${item.email}`) ?? [];
  const selectedUser = reference?.users.find((item) => String(item.id) === userId);

  function extractId(value: string) {
    return value.split("|")[0].trim();
  }

  return (
    <div className="grid">
      <div className="grid forms">
        <FormPanel title="Edit Seller" icon={<Save size={18} />} onSubmit={(event) => {
          event.preventDefault();
          submitJson(`/v1/admin/sellers/${sellerId}`, { name: sellerName }, "Seller updated");
        }}>
          <Select label="Seller" value={sellerOptions.find((item) => item.startsWith(`${sellerId} `)) ?? ""} onChange={(value) => setSellerId(extractId(value))} options={sellerOptions} placeholder="Create a seller first" />
          <Input label="New seller name" value={sellerName} onChange={setSellerName} />
          <button className="primary" disabled={!sellerId || !sellerName} type="submit">Update Seller</button>
        </FormPanel>
        <FormPanel title="Edit Warehouse" icon={<Warehouse size={18} />} onSubmit={(event) => {
          event.preventDefault();
          submitJson(`/v1/admin/warehouses/${warehouseId}`, { name: warehouseName, city: warehouseCity, state: warehouseState }, "Warehouse updated");
        }}>
          <Select label="Warehouse" value={warehouseOptions.find((item) => item.startsWith(`${warehouseId} `)) ?? ""} onChange={(value) => setWarehouseId(extractId(value))} options={warehouseOptions} placeholder="Create a warehouse first" />
          <Input label="Name" value={warehouseName} onChange={setWarehouseName} />
          <Input label="City" value={warehouseCity} onChange={setWarehouseCity} />
          <Input label="State" value={warehouseState} onChange={setWarehouseState} />
          <button className="primary" disabled={!warehouseId || !warehouseName || !warehouseCity || !warehouseState} type="submit">Update Warehouse</button>
        </FormPanel>
      </div>
      <div className="grid forms">
        <FormPanel title="Edit Product" icon={<PackagePlus size={18} />} onSubmit={(event) => {
          event.preventDefault();
          submitJson(`/v1/admin/products/${productId}`, { name: productName, category: productCategory, upc: productUpc }, "Product updated");
        }}>
          <Select label="Product" value={productOptions.find((item) => item.startsWith(`${productId} `)) ?? ""} onChange={(value) => setProductId(extractId(value))} options={productOptions} placeholder="Create a product first" />
          <Input label="Product name" value={productName} onChange={setProductName} />
          <Input label="Category" value={productCategory} onChange={setProductCategory} />
          <Input label="UPC - Universal Product Code / barcode" value={productUpc} onChange={setProductUpc} />
          <button className="primary" disabled={!productId || !productName || !productCategory || !productUpc} type="submit">Update Product</button>
        </FormPanel>
        <FormPanel title="Edit Bin" icon={<MapPin size={18} />} onSubmit={(event) => {
          event.preventDefault();
          submitJson(`/v1/admin/bins/${binId}`, { zone: binZone, rack: binRack, shelf: binShelf }, "Bin updated");
        }}>
          <Select label="Bin" value={binOptions.find((item) => item.startsWith(`${binId} `)) ?? ""} onChange={(value) => setBinId(extractId(value))} options={binOptions} placeholder="Create a bin first" />
          <Input label="Zone" value={binZone} onChange={setBinZone} />
          <Input label="Rack" value={binRack} onChange={setBinRack} />
          <Input label="Shelf" value={binShelf} onChange={setBinShelf} />
          <button className="primary" disabled={!binId || !binZone || !binRack || !binShelf} type="submit">Update Bin</button>
        </FormPanel>
      </div>
      <SimpleTable title="Users" rows={reference?.users ?? []} columns={["id", "email", "full_name", "role", "active", "seller_code", "warehouse_codes"]} />
      <FormPanel title="Manage User" icon={<UserPlus size={18} />} onSubmit={(event) => {
        event.preventDefault();
        submitJson(
          `/v1/admin/users/${userId}`,
          {
            full_name: userFullName,
            role: userRole,
            seller_code: userRole === "SELLER_VIEWER" ? editSellerCode : null,
            warehouse_codes: ["WAREHOUSE_MANAGER", "RECEIVER", "PICKER_PACKER"].includes(userRole) ? [editWarehouseCode] : [],
          },
          "User updated"
        );
      }}>
        <Select label="User" value={userOptions.find((item) => item.startsWith(`${userId} `)) ?? ""} onChange={(value) => setUserId(extractId(value))} options={userOptions} placeholder="Create a user first" />
        <Input label="Full name" value={userFullName} onChange={setUserFullName} />
        <Select label="Role" value={userRole} onChange={setUserRole} options={roles} />
        {userRole === "SELLER_VIEWER" && <Select label="Seller access" value={editSellerCode} onChange={setEditSellerCode} options={reference?.sellers.map((item) => item.code) ?? []} placeholder="Create a seller first" />}
        {["WAREHOUSE_MANAGER", "RECEIVER", "PICKER_PACKER"].includes(userRole) && (
          <Select label="Warehouse access" value={editWarehouseCode} onChange={setEditWarehouseCode} options={reference?.warehouses.map((item) => item.code) ?? []} placeholder="Create a warehouse first" />
        )}
        <button className="primary" disabled={!userId || !userFullName} type="submit">Update User</button>
        <Input label="New password" value={userPassword} onChange={setUserPassword} />
        <button type="button" disabled={!userId || !userPassword} onClick={() => submitJson(`/v1/admin/users/${userId}/reset-password`, { password: userPassword }, "Password reset")}>Reset Password</button>
        <button type="button" disabled={!userId} onClick={() => submitJson(`/v1/admin/users/${userId}/active`, { active: selectedUser?.active ? false : true }, selectedUser?.active ? "User deactivated" : "User activated")}>
          {selectedUser?.active ? "Deactivate User" : "Activate User"}
        </button>
      </FormPanel>
    </div>
  );
}

function AdminSettingsPanel({ settings, submitJson }: { settings: AdminSettings | null; submitJson: SubmitJson }) {
  const [organizationName, setOrganizationName] = useState(settings?.organization_name ?? "");
  const [defaultCarrier, setDefaultCarrier] = useState(settings?.default_carrier ?? "");
  const [lowStockThreshold, setLowStockThreshold] = useState(String(settings?.low_stock_threshold ?? 5));
  const [marketplaceProvider, setMarketplaceProvider] = useState(settings?.marketplace_provider ?? "");
  const [carrierProvider, setCarrierProvider] = useState(settings?.carrier_provider ?? "");
  return (
    <FormPanel title="Organization, Integrations, AI, Policies" icon={<Save size={18} />} onSubmit={(event) => {
      event.preventDefault();
      submitJson("/v1/admin/settings", {
        organization_name: organizationName,
        default_carrier: defaultCarrier,
        low_stock_threshold: Number(lowStockThreshold),
        marketplace_provider: marketplaceProvider,
        marketplace_status: marketplaceProvider ? "CONFIGURED_PENDING_KEYS" : "NOT_CONFIGURED",
        carrier_provider: carrierProvider,
        carrier_status: carrierProvider ? "CONFIGURED_PENDING_KEYS" : "NOT_CONFIGURED",
        ai_document_extraction: false,
        ai_voice_commands: false,
        ai_rag_assistant: false,
        policy_require_receipt_reference: true,
        policy_require_pick_scan: true,
      }, "Settings saved");
    }}>
      <div className="row">
        <Input label="Organization name" value={organizationName} onChange={setOrganizationName} />
        <Input label="Default carrier" value={defaultCarrier} onChange={setDefaultCarrier} />
      </div>
      <div className="row">
        <Input label="Marketplace provider" value={marketplaceProvider} onChange={setMarketplaceProvider} />
        <Input label="Carrier provider" value={carrierProvider} onChange={setCarrierProvider} />
      </div>
      <Input label="Low stock threshold" value={lowStockThreshold} onChange={setLowStockThreshold} />
      <button className="primary" type="submit">Save Settings</button>
    </FormPanel>
  );
}

function ReportsPanel({ token }: { token: string }) {
  const reports = ["inventory", "orders", "receiving", "movements"];
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Reports Export</h2>
        <Download size={18} />
      </div>
      <div className="panel-body report-actions">
        {reports.map((report) => (
          <a key={report} href={`${API_BASE}/v1/admin/reports/${report}.csv?token=${encodeURIComponent(token)}`} onClick={(event) => event.preventDefault()}>
            <button type="button" onClick={() => downloadReport(report, token)}>
              <Download size={16} />
              {report}.csv
            </button>
          </a>
        ))}
      </div>
    </div>
  );
}

async function downloadReport(report: string, token: string) {
  const response = await fetch(`${API_BASE}/v1/admin/reports/${report}.csv`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${report}.csv`;
  anchor.click();
  window.URL.revokeObjectURL(url);
}
