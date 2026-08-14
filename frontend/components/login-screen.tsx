"use client";

import { LockKeyhole, Warehouse } from "lucide-react";
import { FormEvent, useState } from "react";

export function LoginScreen({
  onLogin,
  error,
}: {
  onLogin: (email: string, password: string) => Promise<void>;
  error: string;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await onLogin(email, password);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-hero">
        <div className="hero-mark">
          <Warehouse size={42} />
        </div>
        <h1>Whitfield WMS</h1>
        <p>Role based warehouse operations for receiving, fulfillment, inventory control, documents, and audit.</p>
        <div className="hero-flow">
          <span>Receive</span>
          <span>Reserve</span>
          <span>Pick</span>
          <span>Ship</span>
        </div>
      </section>
      <form className="login-panel" onSubmit={submit}>
        <div>
          <span className="eyebrow">Secure workspace</span>
          <h2>Login</h2>
        </div>
        <label>
          <span>Email</span>
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" placeholder="name@company.com" required />
        </label>
        <label>
          <span>Password</span>
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
        </label>
        <button className="primary" disabled={busy} type="submit">
          <LockKeyhole size={16} />
          {busy ? "Signing in" : "Sign in"}
        </button>
        {error && <div className="notice error">{error}</div>}
      </form>
    </main>
  );
}
