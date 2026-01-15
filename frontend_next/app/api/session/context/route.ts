import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * SESSION CONTEXT — SINGLE SOURCE OF TRUTH
 */

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  // 🔒 FIX: use the SAME backend env as fetcher
  const backend =
    `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/session/context`;

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

  const adminViewCookie = req.cookies.get("admin_view")?.value;

  if (data?.user?.role === "admin") {
    data.is_admin = true;
    data.admin_view =
      adminViewCookie === undefined ? true : adminViewCookie === "true";
  } else {
    data.is_admin = false;
    data.admin_view = false;
  }

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
