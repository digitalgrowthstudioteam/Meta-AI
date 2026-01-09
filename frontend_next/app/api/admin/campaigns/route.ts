import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  const url = new URL(req.url);
  const ai_active = url.searchParams.get("ai_active");
  const user_id = url.searchParams.get("user_id");

  let backendUrl = `${BACKEND_URL}/admin/campaigns`;

  const params = new URLSearchParams();
  if (ai_active !== null) params.append("ai_active", ai_active);
  if (user_id) params.append("user_id", user_id);

  if (params.toString()) {
    backendUrl += `?${params.toString()}`;
  }

  const res = await fetch(backendUrl, {
    method: "GET",
    headers: {
      Cookie: cookie,
    },
    credentials: "include",
    cache: "no-store",
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
