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
  const isAdmin = data?.user?.role === "admin" || data?.user?.is_admin === true;

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
  //  🔑 ROLE COOKIE MANAGEMENT (drives middleware)
  // =====================================================

  const response = NextResponse.json(data, { status: res.status });

  if (!data.user) {
    // No session → remove cookie
    response.cookies.delete("meta_ai_role");
  } else {
    // Set role cookie for middleware/admin logic
    response.cookies.set("meta_ai_role", isAdmin ? "admin" : "user", {
      httpOnly: false,
      sameSite: "lax",
      path: "/",
    });
  }

  return response;
}
