import { NextResponse } from "next/server";

export async function GET() {
  const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/billing/providers/config`, {
    credentials: "include",
  });
  const data = await r.json();
  return NextResponse.json(data);
}

export async function POST(request: Request) {
  const body = await request.json();
  const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/billing/providers/config`, {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  const data = await r.json();
  return NextResponse.json(data);
}
