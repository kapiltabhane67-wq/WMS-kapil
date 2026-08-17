"use client";

import { LockKeyhole, Warehouse, Eye, EyeOff, ArrowLeft, Zap, Shield, BarChart3, Package } from "lucide-react";
import { FormEvent, useState } from "react";

export function LoginScreen({
  onLogin,
  error,
  onBack,
}: {
  onLogin: (email: string, password: string) => Promise<void>;
  error: string;
  onBack?: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [focused, setFocused] = useState<"email" | "password" | null>(null);

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
      {/* Left panel */}
      <section className="login-hero">
        {/* Animated background orbs */}
        <div className="lh-orb lh-orb-1" />
        <div className="lh-orb lh-orb-2" />
        <div className="lh-orb lh-orb-3" />
        <div className="lh-grid" />

        {onBack && (
          <button className="login-back-btn" onClick={onBack} type="button">
            <ArrowLeft size={16} />
            Back to home
          </button>
        )}

        <div className="login-hero-content">
          <div className="hero-mark">
            <Warehouse size={42} />
          </div>
          <h1>Whitfield WMS</h1>
          <p>Role-based warehouse operations for receiving, fulfillment, inventory control, documents, and audit.</p>
          <div className="hero-flow">
            {["Receive", "Reserve", "Pick", "Ship"].map((step, i) => (
              <span key={step} style={{ animationDelay: `${i * 120}ms` }}>
                {step}
              </span>
            ))}
          </div>

          {/* Feature pills */}
          <div className="login-feature-pills">
            <div className="login-pill">
              <Shield size={13} />
              <span>Role-Based Access</span>
            </div>
            <div className="login-pill">
              <Zap size={13} />
              <span>Real-time Sync</span>
            </div>
            <div className="login-pill">
              <BarChart3 size={13} />
              <span>Live Analytics</span>
            </div>
            <div className="login-pill">
              <Package size={13} />
              <span>Audit Trail</span>
            </div>
          </div>
        </div>

        {/* Floating cards */}
        <div className="login-float-card login-float-card-1">
          <div className="lfc-dot" style={{ background: "#22c55e" }} />
          <div>
            <strong>142</strong>
            <span>Live Orders</span>
          </div>
        </div>
        <div className="login-float-card login-float-card-2">
          <div className="lfc-dot" style={{ background: "#d89216" }} />
          <div>
            <strong>3,891</strong>
            <span>Units in Stock</span>
          </div>
        </div>
      </section>

      {/* Right panel */}
      <form className="login-panel" onSubmit={submit}>
        <div className="login-panel-inner">
          <div className="login-panel-header">
            <span className="eyebrow">Secure workspace</span>
            <h2>Welcome back</h2>
            <p className="login-hint">Sign in to your WMS account to continue</p>
          </div>

          <div className="login-fields">
            <label className={`login-field ${focused === "email" ? "login-field-focused" : ""} ${email ? "login-field-filled" : ""}`}>
              <span>Email address</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onFocus={() => setFocused("email")}
                onBlur={() => setFocused(null)}
                autoComplete="email"
                placeholder="name@company.com"
                required
              />
              <div className="login-field-bar" />
            </label>

            <label className={`login-field ${focused === "password" ? "login-field-focused" : ""} ${password ? "login-field-filled" : ""}`}>
              <span>Password</span>
              <div className="login-password-wrap">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setFocused("password")}
                  onBlur={() => setFocused(null)}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="login-eye-btn"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <div className="login-field-bar" />
            </label>
          </div>

          <button className="primary login-submit-btn" disabled={busy} type="submit">
            <div className="login-btn-content">
              {busy ? (
                <>
                  <span className="login-spinner" />
                  Signing in…
                </>
              ) : (
                <>
                  <LockKeyhole size={16} />
                  Sign in to Workspace
                </>
              )}
            </div>
            {!busy && <div className="login-btn-shimmer" />}
          </button>

          {error && (
            <div className="notice error login-error">
              <Shield size={14} />
              {error}
            </div>
          )}

          <p className="login-hint login-hint-bottom">
            Access is provisioned by your organisation admin.
          </p>
        </div>
      </form>
    </main>
  );
}
