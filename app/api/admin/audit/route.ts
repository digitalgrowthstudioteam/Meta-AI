import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";
  const backendBase = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/audit`;

  const { searchParams } = new URL(req.url);

  const format = searchParams.get("format");
  const from = searchParams.get("from");
  const to = searchParams.get("to");
  const adminId = searchParams.get("admin_id");
  const action = searchParams.get("action");

  // If CSV export requested, proxy as stream
  if (format === "csv") {
    const params = new URLSearchParams();
    if (from) params.append("from", from);
    if (to) params.append("to", to);
    if (adminId) params.append("admin_id", adminId);
    if (action) params.append("action", action);
    params.append("format", "csv");

    const res = await fetch(`${backendBase}?${params.toString()}`, {
      method: "GET",
      headers: { cookie },
      credentials: "include",
      cache: "no-store",
    });

    const csv = await res.text();

    return new NextResponse(csv, {
      status: res.status,
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=audit_logs.csv",
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
