import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * SESSION CONTEXT — SINGLE SOURCE OF TRUTH
 */
export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  // Backend endpoint (must match login/session backend)
  const backend = `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/api/session/context`;

  const res = await fetch(backend, {
    method: "GET",
    headers: { cookie },
    credentials: "include",
    cache: "no-store",
  });

  const text = await res.text();
  let data: any = {};
  try {
    data = JSON.parse(text);
  } catch {
    data = {};
  }

  // Admin view toggle cookie (optional)
  const adminViewCookie = req.cookies.get("admin_view")?.value;

  // Determine admin role
  const isAdmin =
    data?.user?.role === "admin" || data?.user?.is_admin === true;

  data.is_admin = isAdmin;
  data.admin_view =
    isAdmin && adminViewCookie !== undefined
      ? adminViewCookie === "true"
      : isAdmin;

  // Normalize ad_account for UI
  if (!data.ad_account && data.ad_accounts && data.active_ad_account_id) {
    const active = data.ad_accounts.find(
      (a: any) => a.id === data.active_ad_account_id
    );
    if (active) {
      data.ad_account = {
        id: active.id,
        name: active.name,
        meta_account_id: active.meta_account_id,
      };
    }
  }

  // =====================================================
  // 🔑 FRONTEND COOKIES (DRIVE MIDDLEWARE)
  // =====================================================
  const response = NextResponse.json(data, { status: res.status });

  // ---- ROLE COOKIE ----
  if (!data.user) {
    response.cookies.delete("meta_ai_role");
  } else {
    response.cookies.set("meta_ai_role", isAdmin ? "admin" : "user", {
      httpOnly: false,
      sameSite: "lax",
      path: "/",
    });
  }

  // ---- TRIAL STATUS COOKIE (PHASE-8) ----
  let trialStatus = "none";

  const sub = data?.user?.subscription;
  if (sub) {
    if (sub.status === "trial") trialStatus = "active";
    else if (sub.status === "expired" && sub.is_trial === true) trialStatus = "expired";
  }

  if (!data.user) {
    response.cookies.delete("meta_ai_trial_status");
  } else {
    response.cookies.set("meta_ai_trial_status", trialStatus, {
      httpOnly: false,
      sameSite: "lax",
      path: "/",
    });
  }

  return response;
}
