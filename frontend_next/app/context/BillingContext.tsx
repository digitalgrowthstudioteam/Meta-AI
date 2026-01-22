"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { apiFetch } from "../lib/fetcher";

type BillingState = {
  status: "none" | "trial" | "grace" | "expired" | "active";
  trial_days_left: number | null;
  grace_days_left: number | null;
  block: {
    soft_block: boolean;
    hard_block: boolean;
  };
  loading: boolean;
};

const BillingContext = createContext<BillingState | null>(null);

export function BillingProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<BillingState>({
    status: "none",
    trial_days_left: null,
    grace_days_left: null,
    block: { soft_block: false, hard_block: false },
    loading: true,
  });

  async function loadStatus() {
    try {
      const res = await apiFetch("/api/billing/status", { cache: "no-store" });
      if (res.ok) {
        const json = await res.json();
        setData({
          status: json.status,
          trial_days_left: json.trial_days_left ?? null,
          grace_days_left: json.grace_days_left ?? null,
          block: json.block,
          loading: false,
        });
      } else {
        setData((d) => ({ ...d, loading: false }));
      }
    } catch (e) {
      setData((d) => ({ ...d, loading: false }));
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  return <BillingContext.Provider value={data}>{children}</BillingContext.Provider>;
}

export function useBilling() {
  const ctx = useContext(BillingContext);
  if (!ctx) throw new Error("useBilling must be used inside BillingProvider");
  return ctx;
}
