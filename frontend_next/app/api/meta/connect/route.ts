import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!backendUrl) {
    return NextResponse.json({ error: "API not configured" }, { status: 500 });
  }

  const res = await fetch(`${backendUrl}/meta/connect`, {
    credentials: "include",
  });

  if (!res.ok) {
    return NextResponse.json({ error: "OAuth connect failed" }, { status: 500 });
  }

  const data = await res.json();
  return NextResponse.redirect(data.redirect_url);
}
