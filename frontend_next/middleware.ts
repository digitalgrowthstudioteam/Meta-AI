import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/verify"];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow internals
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/static") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const session = request.cookies.get("meta_ai_session")?.value;
  const role = request.cookies.get("meta_ai_role")?.value; // admin | user

  // 🔒 Require login
  if (!session && !PUBLIC_PATHS.includes(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 🔒 HARD ADMIN ROUTE PROTECTION
  if (pathname.startsWith("/admin") && role !== "admin") {
    const dashboardUrl = request.nextUrl.clone();
    dashboardUrl.pathname = "/dashboard";
    return NextResponse.redirect(dashboardUrl);
  }

  // ✅ DO NOT auto-redirect admin anywhere
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
