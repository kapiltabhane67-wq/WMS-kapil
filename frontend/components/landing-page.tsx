"use client";

import { useEffect, useRef, useState } from "react";
import {
  Warehouse,
  Package,
  ClipboardList,
  TrendingUp,
  Shield,
  Zap,
  ArrowRight,
  CheckCircle,
  BarChart3,
  Truck,
  ScanLine,
  Users,
  ChevronDown,
  Lock,
} from "lucide-react";

interface LandingPageProps {
  onEnter: () => void;
}

const features = [
  { icon: Package,       title: "Smart Inventory",    desc: "Real-time stock with a movement ledger. Every change is auditable and immutable.", color: "#0f766e" },
  { icon: ClipboardList, title: "Order Management",   desc: "Multi-seller order processing with duplicate protection and instant reservation.",  color: "#d89216" },
  { icon: ScanLine,      title: "Pick & Pack",         desc: "Guided picker tasks with barcode scanning for zero-error fulfillment.",             color: "#7c3aed" },
  { icon: Truck,         title: "Dispatch & Ship",     desc: "Instant label generation, tracking updates, and stock deduction on dispatch.",       color: "#0891b2" },
  { icon: BarChart3,     title: "Analytics Console",   desc: "Live KPIs, throughput metrics, and capacity alerts for warehouse managers.",         color: "#059669" },
  { icon: Shield,        title: "Full Audit Trail",    desc: "Immutable inventory movement logs. Complete compliance and traceability.",            color: "#e11d48" },
];

const stats = [
  { value: "99.9%", label: "Uptime SLA" },
  { value: "<50ms", label: "API Response" },
  { value: "100%", label: "Audit Coverage" },
  { value: "6", label: "Role Types" },
];

const flow = [
  { step: "01", title: "Receive",  desc: "Inbound goods arrive, scanned and binned instantly" },
  { step: "02", title: "Reserve",  desc: "Stock locked the moment an order is placed" },
  { step: "03", title: "Pick",     desc: "Guided pick task sent to the warehouse floor" },
  { step: "04", title: "Pack",     desc: "Invoice & label metadata generated automatically" },
  { step: "05", title: "Dispatch", desc: "Stock deducted, tracking status updated in real-time" },
];

function useInView(ref: React.RefObject<HTMLElement | null>, threshold = 0.15) {
  const [inView, setInView] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setInView(true); },
      { threshold }
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [ref, threshold]);
  return inView;
}

function Section({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref as React.RefObject<HTMLElement>);
  return (
    <section ref={ref} className={`landing-section ${inView ? "ls-visible" : ""} ${className}`}>
      {children}
    </section>
  );
}

export function LandingPage({ onEnter }: LandingPageProps) {
  const [scrollY, setScrollY] = useState(0);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [heroVisible, setHeroVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setHeroVisible(true), 100);
    const onScroll = () => setScrollY(window.scrollY);
    const onMouse = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth - 0.5) * 2,
        y: (e.clientY / window.innerHeight - 0.5) * 2,
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("mousemove", onMouse, { passive: true });
    return () => {
      clearTimeout(t);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("mousemove", onMouse);
    };
  }, []);

  return (
    <div className="ld-root">
      {/* ── BACKGROUND ── */}
      <div className="ld-bg">
        <div className="ld-orb ld-orb-1" />
        <div className="ld-orb ld-orb-2" />
        <div className="ld-orb ld-orb-3" />
        <div className="ld-particles">
          {Array.from({ length: 24 }).map((_, i) => (
            <div key={i} className="ld-particle" style={{
              left: `${(i * 37 + 11) % 100}%`,
              top:  `${(i * 53 + 7)  % 100}%`,
              animationDelay: `${(i * 0.3) % 4}s`,
              animationDuration: `${3 + (i % 4)}s`,
            }} />
          ))}
        </div>
        <div className="ld-grid" />
      </div>

      {/* ── NAVBAR ── */}
      <nav className={`ld-nav ${scrollY > 30 ? "ld-nav-glass" : ""}`}>
        <div className="ld-nav-inner">
          <div className="ld-brand">
            <div className="ld-brand-icon"><Warehouse size={18} /></div>
            <span>Whitfield <strong>WMS</strong></span>
          </div>
          <div className="ld-nav-links">
            <a href="#features">Features</a>
            <a href="#flow">How it works</a>
            <a href="#roles">Roles</a>
          </div>
          <button className="ld-nav-btn" onClick={onEnter}>
            Sign In <ArrowRight size={14} />
          </button>
        </div>
      </nav>

      {/* ── HERO ── */}
      <div className={`ld-hero ${heroVisible ? "ld-hero-in" : ""}`}>
        <div className="ld-hero-badge">
          <Zap size={12} />
          <span>Multi-seller Warehouse Management System</span>
        </div>

        <h1 className="ld-hero-title">
          Warehouse Operations<br />
          <span className="ld-hero-accent">Reimagined</span>
        </h1>

        <p className="ld-hero-sub">
          From receiving dock to final dispatch — every movement tracked,
          every stock change ledgered, zero discrepancies guaranteed.
        </p>

        <div className="ld-hero-btns">
          <button className="ld-btn-primary" onClick={onEnter}>
            <span>Enter Platform</span>
            <ArrowRight size={16} />
          </button>
          <a className="ld-btn-ghost" href="#flow">
            How it works <ChevronDown size={14} />
          </a>
        </div>

        {/* Workflow pills */}
        <div className="ld-flow-pills">
          {["Receive", "Reserve", "Pick", "Pack", "Ship"].map((s, i) => (
            <div key={s} className="ld-pill" style={{ animationDelay: `${0.6 + i * 0.1}s` }}>
              <CheckCircle size={11} /> {s}
            </div>
          ))}
        </div>

        {/* ── 3D MOCKUP ── */}
        <div
          className="ld-mockup-wrap"
          style={{
            transform: `perspective(1200px) rotateX(${mousePos.y * -4}deg) rotateY(${mousePos.x * 6}deg)`,
          }}
        >
          <div className="ld-mockup">
            <div className="ld-mockup-bar">
              <span className="ld-dot" style={{ background: "#ff5f57" }} />
              <span className="ld-dot" style={{ background: "#febc2e" }} />
              <span className="ld-dot" style={{ background: "#28c840" }} />
              <span className="ld-mockup-url">whitfieldwms.com / dashboard</span>
            </div>
            <div className="ld-mockup-body">
              <div className="ld-mockup-side">
                {["Dashboard", "Orders", "Inventory", "Fulfillment", "Receiving", "Ledger"].map((item, i) => (
                  <div key={item} className={`ld-mockup-nav ${i === 0 ? "active" : ""}`}>
                    <span className="ld-mockup-nav-dot" />
                    {item}
                  </div>
                ))}
              </div>
              <div className="ld-mockup-main">
                <div className="ld-mockup-kpis">
                  {[
                    { label: "Live Orders", val: "142", color: "#0f766e" },
                    { label: "In Stock",    val: "3,891", color: "#d89216" },
                    { label: "Picking",     val: "23", color: "#7c3aed" },
                    { label: "Shipped",     val: "67", color: "#059669" },
                  ].map(k => (
                    <div key={k.label} className="ld-kpi" style={{ borderTop: `2px solid ${k.color}` }}>
                      <strong style={{ color: k.color }}>{k.val}</strong>
                      <small>{k.label}</small>
                    </div>
                  ))}
                </div>
                <div className="ld-mockup-chart">
                  {[55, 75, 45, 88, 65, 92, 60, 82, 70, 98, 74, 85].map((h, i) => (
                    <div
                      key={i}
                      className="ld-bar"
                      style={{ height: `${h}%`, animationDelay: `${0.8 + i * 0.05}s` }}
                    />
                  ))}
                </div>
                <div className="ld-mockup-table-head">
                  <span>Order ID</span><span>Status</span><span>SKU</span><span>Qty</span>
                </div>
                {[
                  ["#WH-4821", "Picking", "SKU-109", "12"],
                  ["#WH-4820", "Packed",  "SKU-204", "4"],
                  ["#WH-4819", "Shipped", "SKU-055", "20"],
                ].map(row => (
                  <div key={row[0]} className="ld-mockup-row">
                    {row.map((cell, ci) => <span key={ci}>{cell}</span>)}
                  </div>
                ))}
              </div>
            </div>
          </div>
          {/* 3D shadow/reflection */}
          <div className="ld-mockup-shadow" />
        </div>

        <div className="ld-scroll-hint">
          <ChevronDown size={18} />
          <span>Scroll to explore</span>
        </div>
      </div>

      {/* ── STATS STRIP ── */}
      <div className="ld-stats-strip">
        {stats.map(s => (
          <div key={s.label} className="ld-stat">
            <strong>{s.value}</strong>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {/* ── FEATURES ── */}
      <Section className="ld-features-section" id="features">
        <div className="ld-section-label">CAPABILITIES</div>
        <h2 className="ld-section-title">Everything your warehouse needs</h2>
        <p className="ld-section-sub">A complete operational suite for modern fulfilment centres</p>
        <div className="ld-features-grid">
          {features.map((f, i) => (
            <div key={f.title} className="ld-feature-card" style={{ animationDelay: `${i * 80}ms` }}>
              <div className="ld-feature-icon" style={{ background: `${f.color}18`, color: f.color }}>
                <f.icon size={24} />
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
              <div className="ld-feature-glow" style={{ background: f.color }} />
            </div>
          ))}
        </div>
      </Section>

      {/* ── HOW IT WORKS ── */}
      <Section className="ld-flow-section" id="flow">
        <div className="ld-section-label ld-label-light">THE FLOW</div>
        <h2 className="ld-section-title ld-title-light">From dock to delivery</h2>
        <p className="ld-section-sub ld-sub-light">Five steps, zero guesswork, full traceability</p>
        <div className="ld-flow-grid">
          {flow.map((f, i) => (
            <div key={f.step} className="ld-flow-card" style={{ animationDelay: `${i * 100}ms` }}>
              <div className="ld-flow-num">{f.step}</div>
              {i < flow.length - 1 && <div className="ld-flow-line" />}
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* ── ROLES ── */}
      <Section id="roles">
        <div className="ld-section-label">ACCESS CONTROL</div>
        <h2 className="ld-section-title">Built for every team member</h2>
        <p className="ld-section-sub">Role-based access keeps every user focused and secure</p>
        <div className="ld-roles-grid">
          {[
            { icon: Users,    role: "Org Admin",          perms: ["Full setup access", "Audit logs", "User management", "Admin settings"] },
            { icon: BarChart3, role: "Warehouse Manager",  perms: ["Manager console", "All operations", "Reports & analytics"] },
            { icon: Package,  role: "Receiver",            perms: ["Inbound receipts", "Inventory view", "Audit access"] },
            { icon: ScanLine, role: "Picker / Packer",     perms: ["Pick tasks", "Order scanning", "Fulfillment flow"] },
            { icon: TrendingUp, role: "Seller Viewer",     perms: ["Own inventory", "Order status", "Documents & reports"] },
          ].map((r, i) => (
            <div key={r.role} className="ld-role-card" style={{ animationDelay: `${i * 80}ms` }}>
              <div className="ld-role-icon"><r.icon size={20} /></div>
              <strong>{r.role}</strong>
              <ul>
                {r.perms.map(p => (
                  <li key={p}><CheckCircle size={10} /> {p}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Section>

      {/* ── CTA ── */}
      <div className="ld-cta">
        <div className="ld-cta-orb" />
        <Lock size={28} className="ld-cta-icon" />
        <h2>Ready to take control of your warehouse?</h2>
        <p>Sign in to your Whitfield WMS workspace and manage operations in real time.</p>
        <button className="ld-btn-primary ld-btn-lg" onClick={onEnter}>
          <Warehouse size={20} />
          <span>Enter the Platform</span>
          <ArrowRight size={18} />
        </button>
      </div>

      {/* ── FOOTER ── */}
      <footer className="ld-footer">
        <div className="ld-brand">
          <div className="ld-brand-icon"><Warehouse size={15} /></div>
          <span>Whitfield <strong>WMS</strong></span>
        </div>
        <span className="ld-footer-copy">© 2026 Whitfield Fulfillment · All rights reserved</span>
      </footer>
    </div>
  );
}
