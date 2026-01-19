import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/verify"];

// 🔓 Razorpay/Webhook bypass
const WEBHOOK_PATHS = ["/billing/webhook"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 🔓 Allow webhook paths through without auth or redirects
  if (WEBHOOK_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // System/static/assets → always allow
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/static") ||
    pathname.startsWith("/favicon.ico") ||
    pathname.startsWith("/manifest") ||
    pathname.startsWith("/robots.txt") ||
    pathname.startsWith("/sitemap") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Cookies
  const sessionCookie = request.cookies.get("meta_ai_session")?.value;
  const roleCookie = request.cookies.get("meta_ai_role")?.value;

  // =====================================================
  // 🔒 ADMIN PROTECTION
  // =====================================================
  if (pathname.startsWith("/admin")) {
    // Not logged in → go login
    if (!sessionCookie) {
      const loginUrl = request.nextUrl.clone();
      loginUrl.pathname = "/login";
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }

    // Role not loaded yet (first request) → allow & backend will set role cookie
    if (!roleCookie) {
      return NextResponse.next();
    }

    // Logged in but not admin → redirect to dashboard
    if (roleCookie !== "admin") {
      const dashUrl = request.nextUrl.clone();
      dashUrl.pathname = "/dashboard";
      return NextResponse.redirect(dashUrl);
    }

    // Admin authenticated
    return NextResponse.next();
  }

  // =====================================================
  // 🔐 PUBLIC ROUTES
  // =====================================================
  if (!sessionCookie && !PUBLIC_PATHS.includes(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // If logged in but on login/home → send to dashboard
  if (sessionCookie && (pathname === "/" || pathname === "/login")) {
    const dashUrl = request.nextUrl.clone();
    dashUrl.pathname = "/dashboard";
    return NextResponse.redirect(dashUrl);
  }

  return NextResponse.next();
}

// =====================================================
// ⚙️ CONFIG (exclude APIs and static assets)
// =====================================================
export const config = {
  matcher: [
    "/((?!_next|static|favicon.ico|manifest|robots.txt|sitemap|api).*)",
  ],
};
