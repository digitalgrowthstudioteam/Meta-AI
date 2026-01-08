import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";

  const backend = `${process.env.NEXT_PUBLIC_BACKEND_URL}/session/context`;

  const res = await fetch(backend, {
    method: "GET",
    headers: {
      cookie,
    },
    credentials: "include",
    cache: "no-store",
  });

  const text = await res.text();

  let data = {};
  try {
    data = JSON.parse(text);
  } catch {}

  return NextResponse.json(data, { status: res.status });
}
