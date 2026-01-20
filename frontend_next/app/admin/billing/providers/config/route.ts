import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  const r = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/billing/providers/config`, {
    method: "GET",
    headers: {
      "Cookie": cookie,
    },
    cache: "no-store",
  });

  const text = await r.text();
  let data: any = {};

  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }

  return NextResponse.json(data, { status: r.status });
}

export async function POST(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";
  const body = await req.json();

  const r = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/billing/providers/config`, {
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
