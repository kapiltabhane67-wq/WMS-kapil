"use client";

import { RefreshCcw } from "lucide-react";
import { FormEvent, useState } from "react";

import { allNavItems } from "../lib/constants";
import type { User, View } from "../lib/types";
import { ChatWidget } from "./chat-widget";


export function AppShell({
  view,
  setView,
  me,
  role,
  token,
  children,
  refresh,
  logout,
  changePassword,
}: {
  view: View;
  setView: (view: View) => void;
  me: User | null;
  role: string;
  token: string;
  children: React.ReactNode;
  refresh: () => void;
  logout: () => Promise<void> | void;
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
}) {
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = allNavItems.filter((item) => {
    if (item[0] === "setup") return role === "ORG_ADMIN";
    if (item[0] === "manager") return ["ORG_ADMIN", "WAREHOUSE_MANAGER"].includes(role);
    if (item[0] === "seller") return role === "SELLER_VIEWER";
    if (role === "RECEIVER") return ["dashboard", "receiving", "inventory", "audit"].includes(item[0]);
    if (role === "PICKER_PACKER") return ["dashboard", "fulfillment", "orders"].includes(item[0]);
    if (role === "SELLER_VIEWER") return ["seller", "dashboard", "orders", "inventory", "documents", "audit"].includes(item[0]);
    return true;
  });

  async function submitPasswordChange(event: FormEvent) {
    event.preventDefault();
    setPasswordMessage("");
    setPasswordError("");
    setBusy(true);
    try {
      const changed = await changePassword(currentPassword, newPassword);
      if (changed) {
        setPasswordMessage("Password changed. Please sign in again.");
        setCurrentPassword("");
        setNewPassword("");
      } else {
        setPasswordError("Password change failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">Whitfield WMS</div>
        <div className="session-card">
          <span>Signed in</span>
          <strong>{me?.full_name ?? "Whitfield user"}</strong>
          <small>{me?.email}</small>
          <button type="button" onClick={() => setShowPasswordForm((current) => !current)}>
            Change password
          </button>
          {showPasswordForm && (
            <form className="password-card" onSubmit={submitPasswordChange}>
              <input
                type="password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                placeholder="Current password"
                required
              />
              <input
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                placeholder="New password"
                minLength={8}
                required
              />
              <button type="submit" disabled={busy}>{busy ? "Updating" : "Update password"}</button>
              {passwordMessage && <small>{passwordMessage}</small>}
              {passwordError && <small className="danger-text">{passwordError}</small>}
            </form>
          )}
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
      <ChatWidget token={token} role={role} />
    </main>
  );
}
