import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const backendUrl = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/dashboard`;

  const res = await fetch(backendUrl, {
    method: "GET",
    headers: {
      cookie: request.headers.get("cookie") || "",
    },
    credentials: "include",
    cache: "no-store",
  });

  const text = await res.text();

  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}
