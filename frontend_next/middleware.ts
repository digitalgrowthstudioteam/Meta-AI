import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/verify"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

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

  // Read cookies
  const sessionCookie = request.cookies.get("meta_ai_session")?.value;
  const roleCookie = request.cookies.get("meta_ai_role")?.value;

  // =====================================================
  //  🧩 WRITE CURRENT PATH FOR SSR LAYOUT USE
  // =====================================================
  const response = NextResponse.next();
  response.cookies.set("next-url", pathname, {
    httpOnly: false,
    sameSite: "lax",
    path: "/",
  });

  // =====================================================
  //  🔒 ADMIN PROTECTION — ALLOW CONTEXT SYNC FIRST
  // =====================================================
  if (pathname.startsWith("/admin")) {
    // Not logged in → go login
    if (!sessionCookie) {
      const loginUrl = request.nextUrl.clone();
      loginUrl.pathname = "/login";
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }

    // Logged in but role not synced yet → allow to continue & let backend set cookies
    if (!roleCookie) {
      return response;
    }

    // Logged in but not admin → go dashboard
    if (roleCookie !== "admin") {
      const dashUrl = request.nextUrl.clone();
      dashUrl.pathname = "/dashboard";
      return NextResponse.redirect(dashUrl);
    }

    // Admin allowed
    return response;
  }

  // =====================================================
  //  🔐 PUBLIC ROUTES
  // =====================================================
  if (!sessionCookie && !PUBLIC_PATHS.includes(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Logged in but on login/home → send to dashboard
  if (sessionCookie && (pathname === "/" || pathname === "/login")) {
    const dashUrl = request.nextUrl.clone();
    dashUrl.pathname = "/dashboard";
    return NextResponse.redirect(dashUrl);
  }

  return response;
}

// =====================================================
//  ⚙️ CONFIG (exclude APIs, runtime assets)
// =====================================================
export const config = {
  matcher: [
    "/((?!_next|static|favicon.ico|manifest|robots.txt|sitemap|api).*)",
  ],
};
