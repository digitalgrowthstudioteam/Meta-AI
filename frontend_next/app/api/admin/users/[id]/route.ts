import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const userId = params.id;

  const backendUrl = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/users`;

  const res = await fetch(backendUrl, {
    method: "GET",
    headers: {
      cookie: request.headers.get("cookie") || "",
    },
    credentials: "include",
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json({ error: "Backend error" }, { status: res.status });
  }

  const users = await res.json();
  const user = users.find((u: any) => u.id === userId);

  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  // Minimal payload to keep UI working
  return NextResponse.json(
    {
      user,
      meta_accounts: [],
      campaigns: [],
      invoices: [],
      ai_actions: [],
    },
    { status: 200 }
  );
}
