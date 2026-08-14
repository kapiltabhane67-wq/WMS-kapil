"use client";

import { useEffect, useMemo, useState } from "react";

import { LoginScreen } from "../components/login-screen";
import { AppShell } from "../components/shell";
import { allNavItems } from "../lib/constants";
import { api, login } from "../lib/api";
import type { AdminSettings, AppData, AuditLogRow, Dashboard, DocumentRow, InventoryRow, ManagerConsole, MovementRow, OrderRow, PickTask, ReceiptRow, ReferenceData, User, View } from "../lib/types";
import { DashboardView } from "../features/wms/dashboard-view";
import { DocumentsView } from "../features/wms/documents-view";
import { FulfillmentView } from "../features/wms/fulfillment-view";
import { InventoryView } from "../features/wms/inventory-view";
import { LedgerView } from "../features/wms/ledger-view";
import { ManagerView } from "../features/wms/manager-view";
import { OrdersView } from "../features/wms/orders-view";
import { ReceivingView } from "../features/wms/receiving-view";
import { SellerView } from "../features/wms/seller-view";
import { SetupView } from "../features/wms/setup-view";

const emptyData: AppData = {
  me: null,
  dashboard: null,
  managerConsole: null,
  inventory: [],
  orders: [],
  tasks: [],
  documents: [],
  movements: [],
  receipts: [],
  auditLogs: [],
  settings: null,
  reference: null,
};

function normalizeLoginEmail(email: string) {
  const cleanEmail = email.trim().toLowerCase();
  if (cleanEmail.endsWith("@whitfield.local")) return cleanEmail.replace("@whitfield.local", "@whitfieldwms.com");
  if (cleanEmail.endsWith("@client.local")) return cleanEmail.replace("@client.local", "@client.example.com");
  return cleanEmail;
}

export default function Home() {
  const [token, setToken] = useState("");
  const [view, setView] = useState<View>("dashboard");
  const [data, setData] = useState<AppData>(emptyData);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const role = data.me?.role ?? "";

  const visibleViews = useMemo(() => {
    return allNavItems
      .filter((item) => {
        if (item[0] === "setup") return role === "ORG_ADMIN";
        if (item[0] === "manager") return ["ORG_ADMIN", "WAREHOUSE_MANAGER"].includes(role);
        if (item[0] === "seller") return role === "SELLER_VIEWER";
        if (role === "RECEIVER") return ["dashboard", "receiving", "inventory", "audit"].includes(item[0]);
        if (role === "PICKER_PACKER") return ["dashboard", "fulfillment", "orders"].includes(item[0]);
        if (role === "SELLER_VIEWER") return ["seller", "dashboard", "orders", "inventory", "documents", "audit"].includes(item[0]);
        return true;
      })
      .map((item) => item[0]);
  }, [role]);

  async function loadData() {
    if (!token) return;
    setError("");
    try {
      const [me, reference, dashboard, inventory, documents, movements] = await Promise.all([
        api<User>("/v1/me", token),
        api<ReferenceData>("/v1/reference", token),
        api<Dashboard>("/v1/dashboard", token),
        api<InventoryRow[]>("/v1/inventory", token),
        api<DocumentRow[]>("/v1/documents", token),
        api<MovementRow[]>("/v1/inventory/movements", token),
      ]);
      const orders = ["ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER", "SELLER_VIEWER"].includes(me.role)
        ? await api<OrderRow[]>("/v1/orders", token)
        : [];
      const tasks = ["ORG_ADMIN", "WAREHOUSE_MANAGER", "PICKER_PACKER"].includes(me.role)
        ? await api<PickTask[]>("/v1/fulfillment/pick-tasks", token)
        : [];
      const managerConsole = ["ORG_ADMIN", "WAREHOUSE_MANAGER"].includes(me.role)
        ? await api<ManagerConsole>("/v1/manager/console", token)
        : null;
      const receipts = ["ORG_ADMIN", "WAREHOUSE_MANAGER", "RECEIVER"].includes(me.role)
        ? await api<ReceiptRow[]>("/v1/receiving/receipts", token)
        : [];
      const [auditLogs, settings] = me.role === "ORG_ADMIN"
        ? await Promise.all([
            api<AuditLogRow[]>("/v1/admin/audit-logs", token),
            api<AdminSettings>("/v1/admin/settings", token),
          ])
        : [[], null];
      setData({ me, dashboard, managerConsole, inventory, orders, tasks, documents, movements, receipts, auditLogs, settings, reference });
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unable to load WMS data";
      if (message.includes("Invalid or expired session") || message.includes("Login token is required")) {
        clearSession();
        setError("Your session expired. Please sign in again.");
        return;
      }
      setError(message);
    }
  }

  useEffect(() => {
    const savedToken = window.localStorage.getItem("wms_token");
    if (savedToken) setToken(savedToken);
  }, []);

  useEffect(() => {
    loadData();
  }, [token]);

  useEffect(() => {
    if (!visibleViews.includes(view)) setView("dashboard");
  }, [visibleViews, view]);

  useEffect(() => {
    if (role === "SELLER_VIEWER" && view === "dashboard") setView("seller");
  }, [role, view]);

  async function submitJson<T = unknown>(path: string, payload: object, success: string): Promise<T | null> {
    setMessage("");
    setError("");
    try {
      const result = await api<T>(path, token, { method: "POST", body: JSON.stringify(payload) });
      setMessage(success);
      await loadData();
      return result;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Action failed");
      return null;
    }
  }

  async function handleLogin(email: string, password: string) {
    setError("");
    const loginEmail = normalizeLoginEmail(email);
    try {
      const session = await login(loginEmail, password);
      setToken(session.access_token);
      window.localStorage.setItem("wms_token", session.access_token);
      setData((current) => ({ ...current, me: session.user }));
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Login failed";
      setError(message.includes("Invalid email or password")
        ? "Invalid email or password. If this is a role user, confirm the admin created that user and password."
        : message);
    }
  }

  function clearSession() {
    window.localStorage.removeItem("wms_token");
    setToken("");
    setMessage("");
    setData(emptyData);
  }

  async function logout() {
    if (token) {
      try {
        await api("/v1/auth/logout", token, { method: "POST" });
      } catch {
        // Local session still needs to clear even if the token already expired.
      }
    }
    setError("");
    clearSession();
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    setError("");
    try {
      await api("/v1/auth/change-password", token, {
        method: "POST",
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      await logout();
      return true;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Password change failed");
      return false;
    }
  }

  if (!token) {
    return <LoginScreen onLogin={handleLogin} error={error} />;
  }

  return (
    <AppShell view={view} setView={setView} me={data.me} role={role} refresh={loadData} logout={logout} changePassword={changePassword}>
      {error && <div className="notice error">{error}</div>}
      {message && <div className="notice">{message}</div>}
      {view === "dashboard" && <DashboardView dashboard={data.dashboard} orders={data.orders} inventory={data.inventory} />}
      {view === "setup" && <SetupView reference={data.reference} settings={data.settings} auditLogs={data.auditLogs} submitJson={submitJson} token={token} />}
      {view === "manager" && <ManagerView consoleData={data.managerConsole} />}
      {view === "seller" && (
        <SellerView
          reference={data.reference}
          dashboard={data.dashboard}
          inventory={data.inventory}
          orders={data.orders}
          documents={data.documents}
          movements={data.movements}
        />
      )}
      {view === "receiving" && <ReceivingView reference={data.reference} submitJson={submitJson} inventory={data.inventory} receipts={data.receipts} />}
      {view === "orders" && <OrdersView submitJson={submitJson} orders={data.orders} reference={data.reference} canImport={["ORG_ADMIN", "WAREHOUSE_MANAGER"].includes(role)} />}
      {view === "fulfillment" && <FulfillmentView submitJson={submitJson} tasks={data.tasks} orders={data.orders} />}
      {view === "inventory" && (
        <InventoryView
          inventory={data.inventory}
          reference={data.reference}
          submitJson={submitJson}
          canAdjust={["ORG_ADMIN", "WAREHOUSE_MANAGER"].includes(role)}
        />
      )}
      {view === "documents" && <DocumentsView documents={data.documents} token={token} onUploaded={loadData} />}
      {view === "audit" && <LedgerView movements={data.movements} />}
    </AppShell>
  );
}
