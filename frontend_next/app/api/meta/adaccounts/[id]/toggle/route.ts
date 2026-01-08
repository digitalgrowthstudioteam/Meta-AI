import { NextResponse } from "next/server";

export async function POST(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const cookie = req.headers.get("cookie") || "";

    const backendUrl = `${process.env.NEXT_PUBLIC_BACKEND_URL}/meta/adaccounts/${params.id}/toggle`;

    const res = await fetch(backendUrl, {
      method: "POST",
      // ⬇️ Forward BOTH cookie & Cookie for compatibility
      headers: {
        Cookie: cookie,
        cookie: cookie,
      },
      credentials: "include",
    });

    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json(
      { error: "Toggle failed" },
      { status: 500 }
    );
  }
}
