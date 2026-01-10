import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";
  const backendBase = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/invoices`;

  const { searchParams } = new URL(req.url);

  const format = searchParams.get("format");
  const userId = searchParams.get("user_id");
  const from = searchParams.get("from");
  const to = searchParams.get("to");

  // ZIP export passthrough
  if (format === "zip") {
    const params = new URLSearchParams();
    if (userId) params.append("user_id", userId);
    if (from) params.append("from", from);
    if (to) params.append("to", to);
    params.append("format", "zip");

    const res = await fetch(`${backendBase}?${params.toString()}`, {
      method: "GET",
      headers: { cookie },
      credentials: "include",
      cache: "no-store",
    });

    const zipBuffer = await res.arrayBuffer();

    return new NextResponse(zipBuffer, {
      status: res.status,
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": "attachment; filename=invoices.zip",
      },
    });
  }

  // Default JSON passthrough
  const res = await fetch(backendBase, {
    method: "GET",
    headers: { cookie },
    credentials: "include",
    cache: "no-store",
  });

  const text = await res.text();
  let data: any = {};
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }

  return NextResponse.json(data, { status: res.status });
}
