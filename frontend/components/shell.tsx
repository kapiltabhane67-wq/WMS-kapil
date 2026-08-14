"use client";

import { RefreshCcw } from "lucide-react";

import { allNavItems } from "../lib/constants";
import type { User, View } from "../lib/types";

export function AppShell({
  view,
  setView,
  me,
  role,
  children,
  refresh,
  logout,
}: {
  view: View;
  setView: (view: View) => void;
  me: User | null;
  role: string;
  children: React.ReactNode;
  refresh: () => void;
  logout: () => void;
}) {
  const nav = allNavItems.filter((item) => {
    if (item[0] === "setup") return role === "ORG_ADMIN";
    if (item[0] === "manager") return ["ORG_ADMIN", "WAREHOUSE_MANAGER"].includes(role);
    if (item[0] === "seller") return role === "SELLER_VIEWER";
    if (role === "RECEIVER") return ["dashboard", "receiving", "inventory", "audit"].includes(item[0]);
    if (role === "PICKER_PACKER") return ["dashboard", "fulfillment", "orders"].includes(item[0]);
    if (role === "SELLER_VIEWER") return ["seller", "dashboard", "orders", "inventory", "documents", "audit"].includes(item[0]);
    return true;
  });

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">Whitfield WMS</div>
        <div className="session-card">
          <span>Signed in</span>
          <strong>{me?.full_name ?? "Whitfield user"}</strong>
          <small>{me?.email}</small>
          <button type="button" onClick={logout}>Logout</button>
        </div>
        <div className="nav">
          {nav.map(([key, label, Icon]) => (
            <button key={key} className={view === key ? "active" : ""} onClick={() => setView(key)}>
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>
      </aside>
      <section className="main">
        <div className="topbar">
          <div className="title">
            <h1>{me?.full_name ?? "Whitfield user"}</h1>
            <p>
              <span className="badge">{role}</span>
            </p>
          </div>
          <button onClick={refresh}>
            <RefreshCcw size={16} />
            Refresh
          </button>
        </div>
        {children}
      </section>
    </main>
  );
}
