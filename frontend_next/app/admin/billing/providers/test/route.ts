import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";
  const body = await req.json();

  const r = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/billing/providers/test`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Cookie": cookie,
    },
    body: JSON.stringify(body),
  });

  const text = await r.text();
  let data: any = {};

  try {
    data = JSON.parse(text);
  } catch {
    data = { error: text };
  }

  return NextResponse.json(data, { status: r.status });
}
