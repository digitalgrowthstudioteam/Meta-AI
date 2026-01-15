import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/verify"];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1️⃣ Always allow Next.js internals, APIs, static assets
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/static") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const session = request.cookies.get("meta_ai_session")?.value;
  const role = request.cookies.get("meta_ai_role")?.value; // "admin" | "user"

  // 2️⃣ Block unauthenticated users
  if (!session && !PUBLIC_PATHS.includes(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 3️⃣ 🔒 HARD ADMIN PROTECTION
  if (pathname.startsWith("/admin") && role !== "admin") {
    const userDashboard = request.nextUrl.clone();
    userDashboard.pathname = "/dashboard";
    return NextResponse.redirect(userDashboard);
  }

  // 4️⃣ Logged-in users visiting / or /login → USER dashboard (not admin)
  if (session && (pathname === "/" || pathname === "/login")) {
    const dashboardUrl = request.nextUrl.clone();
    dashboardUrl.pathname = "/dashboard";
    return NextResponse.redirect(dashboardUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
