import {
  BarChart3,
  Boxes,
  ClipboardCheck,
  FileText,
  MonitorCog,
  Store,
  ScanLine,
  Send,
  Settings,
  ShieldCheck,
} from "lucide-react";

import type { View } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8016";

export const allNavItems = [
  ["dashboard", "Dashboard", BarChart3],
  ["setup", "Setup", Settings],
  ["manager", "Manager", MonitorCog],
  ["seller", "Seller Portal", Store],
  ["receiving", "Receiving", ClipboardCheck],
  ["orders", "Orders", Send],
  ["fulfillment", "Fulfillment", ScanLine],
  ["inventory", "Inventory", Boxes],
  ["documents", "Documents", FileText],
  ["audit", "Ledger", ShieldCheck],
] as const satisfies readonly [View, string, typeof BarChart3][];
