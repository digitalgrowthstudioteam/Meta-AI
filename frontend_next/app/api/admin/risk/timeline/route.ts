import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  const backend = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/risk/timeline`;

  const res = await fetch(backend, {
    method: "GET",
    headers: { cookie },
    credentials: "include",
    cache: "no-store",
  });

  const text = await res.text();
  let data: any = [];

  try {
    data = JSON.parse(text);
  } catch {
    data = [];
  }

  return NextResponse.json(data, { status: res.status });
}
