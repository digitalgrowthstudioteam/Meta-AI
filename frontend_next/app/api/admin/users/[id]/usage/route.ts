import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const backend = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/users/${params.id}/usage`;

  const res = await fetch(backend, {
    method: "GET",
    headers: {
      cookie: request.headers.get("cookie") || "",
    },
    credentials: "include",
    cache: "no-store",
  });

  const text = await res.text();
  try {
    return NextResponse.json(JSON.parse(text), { status: res.status });
  } catch {
    return NextResponse.json(text, { status: res.status });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const backend = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/users/${params.id}/usage`;
  const body = await request.json();

  const res = await fetch(backend, {
    method: "POST",
    headers: {
      cookie: request.headers.get("cookie") || "",
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(body),
  });

  const text = await res.text();
  try {
    return NextResponse.json(JSON.parse(text), { status: res.status });
  } catch {
    return NextResponse.json(text, { status: res.status });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const backend = `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/users/${params.id}/usage`;
  const body = await request.json();

  const res = await fetch(backend, {
    method: "DELETE",
    headers: {
      cookie: request.headers.get("cookie") || "",
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(body),
  });

  const text = await res.text();
  try {
    return NextResponse.json(JSON.parse(text), { status: res.status });
  } catch {
    return NextResponse.json(text, { status: res.status });
  }
}

