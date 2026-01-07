import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * SINGLE SOURCE OF TRUTH — SESSION CONTEXT
 * Used by ALL authenticated pages
 */
export async function GET(req: NextRequest) {
  const sessionCookie = req.cookies.get("meta_ai_session")?.value;

  if (!sessionCookie) {
    return NextResponse.json(
      { error: "Not authenticated" },
      { status: 401 }
    );
  }

  const res = await fetch(
    `${process.env.NEXT_PUBLIC_BACKEND_URL}/auth/session-context`,
    {
      headers: {
        // ✅ Forward session token properly
        Authorization: `Bearer ${sessionCookie}`,
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
