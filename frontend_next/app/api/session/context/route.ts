import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * SESSION CONTEXT — SINGLE SOURCE OF TRUTH
 *
 * Responsibilities:
 * - Fetch backend session context
 * - Fetch billing status
 * - Normalize + enrich user data
 * - Set FE cookies:
 *      meta_ai_role = admin/user
 *      meta_ai_block = none|soft|hard
 * - Drive middleware + topbar + overlay UX
 */
export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // ------------------------------
  // 1) SESSION CONTEXT
  // ------------------------------
  const ctxRes = await fetch(`${API}/api/session/context`, {
    method: "GET",
    headers: { cookie },
    credentials: "include",
    cache: "no-store",
  });

  const ctxText = await ctxRes.text();
  let ctx: any = {};
  try {
    ctx = JSON.parse(ctxText);
  } catch {
    ctx = {};
  }

  // ------------------------------
  // 2) BILLING STATUS
  // ------------------------------
  let billing: any = null;
  if (ctx?.user) {
    try {
      const billRes = await fetch(`${API}/billing/status`, {
        method: "GET",
        headers: { cookie },
        credentials: "include",
        cache: "no-store",
      });
      const txt = await billRes.text();
      billing = JSON.parse(txt);
    } catch {
      billing = null;
    }
  }

  // ------------------------------
  // ADMIN ROLE + VIEW
  // ------------------------------
  const adminViewCookie = req.cookies.get("admin_view")?.value;
  const isAdmin =
    ctx?.user?.role === "admin" || ctx?.user?.is_admin === true;

  ctx.is_admin = isAdmin;
  ctx.admin_view =
    isAdmin && adminViewCookie !== undefined
      ? adminViewCookie === "true"
      : isAdmin;

  // ------------------------------
  // AD ACCOUNT NORMALIZATION
  // ------------------------------
  if (!ctx.ad_account && ctx.ad_accounts && ctx.active_ad_account_id) {
    const active = ctx.ad_accounts.find(
      (a: any) => a.id === ctx.active_ad_account_id
    );
    if (active) {
      ctx.ad_account = {
        id: active.id,
        name: active.name,
        meta_account_id: active.meta_account_id,
      };
    }
  }

  // ------------------------------
  // BUILD RESPONSE
  // ------------------------------
  const response = NextResponse.json(
    {
      ...ctx,
      billing,
    },
    {
      status: ctxRes.status,
    }
  );

  // =====================================================
  // 🍪 COOKIES — DRIVE MIDDLEWARE
  // =====================================================

  if (!ctx.user) {
    // user logged out → clear cookies
    response.cookies.delete("meta_ai_role");
    response.cookies.delete("meta_ai_block");
    return response;
  }

  // ---- ROLE COOKIE ----
  response.cookies.set("meta_ai_role", isAdmin ? "admin" : "user", {
    httpOnly: false,
    sameSite: "lax",
    path: "/",
  });

  // ---- BILLING BLOCK COOKIE ----
  // billing.status = trial|active|grace|expired|none
  // billing.block.soft_block = true/false
  // billing.block.hard_block = true/false
  let blockState = "none";

  if (billing?.block?.hard_block) {
    blockState = "hard";
  } else if (billing?.block?.soft_block) {
    blockState = "soft";
  }

  response.cookies.set("meta_ai_block", blockState, {
    httpOnly: false,
    sameSite: "lax",
    path: "/",
  });

  return response;
}
