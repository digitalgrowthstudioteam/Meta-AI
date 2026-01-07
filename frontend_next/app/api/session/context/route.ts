import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * SINGLE SOURCE OF TRUTH — SESSION CONTEXT
 * This endpoint is used by ALL pages
 */
export async function GET(req: NextRequest) {
  const cookie = req.cookies.get("meta_ai_session");

  if (!cookie) {
    return NextResponse.json(
      { error: "Not authenticated" },
      { status: 401 }
    );
  }

  const res = await fetch(
    `${process.env.NEXT_PUBLIC_BACKEND_URL}/auth/session-context`,
    {
      headers: {
        "X-User-Id": cookie.value,
      },
      cache: "no-store",
    }
  );

  if (!res.ok) {
    return NextResponse.json(
      { error: "Failed to load session context" },
      { status: res.status }
    );
  }

  const data = await res.json();
  return NextResponse.json(data);
}
