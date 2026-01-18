import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL;
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");

  if (!code || !state) {
    return NextResponse.json({ error: "Missing OAuth params" }, { status: 400 });
  }

  const res = await fetch(
    `${backendUrl}/meta/oauth/callback?code=${code}&state=${state}`,
    { credentials: "include" }
  );

  if (res.redirected || res.status === 302) {
    return NextResponse.redirect("/campaigns");
  }

  return NextResponse.redirect("/campaigns");
}
