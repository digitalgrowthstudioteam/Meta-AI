import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Forward cookie → Backend `/api/session/context`
 * Returns:
 * - user
 * - ad_accounts[]
 * - active_ad_account_id
 * - ad_account (backward compatibility)
 */
export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  const backend = `${process.env.NEXT_PUBLIC_BACKEND_URL}/session/context`;

  const res = await fetch(backend, {
    method: "GET",
    headers: {
      cookie, // forward cookie to backend
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

  // Ensure backward compatibility for old UI pages
  // If backend returns only ad_accounts[] and active_ad_account_id
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
