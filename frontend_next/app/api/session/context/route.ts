import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * SESSION CONTEXT — SINGLE SOURCE OF TRUTH
 *
 * Adds:
 * - role awareness
 * - admin ↔ user view switch support
 *
 * Rules:
 * - Normal users NEVER see admin mode
 * - Admin can toggle admin_view = true | false
 * - Toggle state stored in cookie (server-trusted)
 */

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  const backend = `${process.env.NEXT_PUBLIC_BACKEND_URL}/session/context`;

  const res = await fetch(backend, {
    method: "GET",
    headers: {
      cookie, // forward auth cookie
    },
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

  /**
   * -------------------------------
   * ADMIN ↔ USER VIEW SWITCH
   * -------------------------------
   * Cookie: admin_view=true|false
   */
  const adminViewCookie = req.cookies.get("admin_view")?.value === "true";

  if (data?.user?.role === "admin") {
    data.is_admin = true;
    data.admin_view = adminViewCookie;
  } else {
    // 🔒 Hard lock for normal users
    data.is_admin = false;
    data.admin_view = false;
  }

  /**
   * -------------------------------
   * BACKWARD COMPATIBILITY
   * -------------------------------
   */
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

  return NextResponse.json(data, { status: res.status });
}
