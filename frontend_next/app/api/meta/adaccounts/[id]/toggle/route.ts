import { NextResponse } from "next/server";

export async function POST(
  _req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const cookie = _req.headers.get("cookie") || "";

    const backend = `${process.env.NEXT_PUBLIC_BACKEND_URL}/meta/adaccounts/${params.id}/toggle`;

    const res = await fetch(backend, {
      method: "POST",
      headers: {
        cookie,
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
