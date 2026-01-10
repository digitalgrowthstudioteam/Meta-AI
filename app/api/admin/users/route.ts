import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";
  const backendBase = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/users`;

  const { searchParams } = new URL(req.url);
  const format = searchParams.get("format"); // json | csv
  const userId = searchParams.get("user_id");

  // GDPR export passthrough (JSON / CSV)
  if (format === "json" || format === "csv") {
    const params = new URLSearchParams();
    if (userId) params.append("user_id", userId);
    params.append("format", format);

    const res = await fetch(`${backendBase}?${params.toString()}`, {
      method: "GET",
      headers: { cookie },
      credentials: "include",
      cache: "no-store",
    });

    if (format === "csv") {
      const csv = await res.text();
      return new NextResponse(csv, {
        status: res.status,
        headers: {
          "Content-Type": "text/csv",
          "Content-Disposition": `attachment; filename=gdpr_user_export.csv`,
        },
      });
    }

    // JSON export
    const json = await res.text();
    return new NextResponse(json, {
      status: res.status,
      headers: {
        "Content-Type": "application/json",
        "Content-Disposition": `attachment; filename=gdpr_user_export.json`,
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
