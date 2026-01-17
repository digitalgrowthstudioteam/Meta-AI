import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/verify"];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow system/static/SSR/asset files
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

  const sessionCookie = request.cookies.get("meta_ai_session")?.value;
  const roleCookie = request.cookies.get("meta_ai_role")?.value;

  // 🔒 ADMIN PROTECTION
  if (pathname.startsWith("/admin")) {
    if (!sessionCookie) {
      const loginUrl = request.nextUrl.clone();
      loginUrl.pathname = "/login";
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }

    if (roleCookie !== "admin") {
      const dashUrl = request.nextUrl.clone();
      dashUrl.pathname = "/dashboard";
      return NextResponse.redirect(dashUrl);
    }

    return NextResponse.next();
  }

  // 🔐 PUBLIC ACCESS CONTROL
  if (!sessionCookie && !PUBLIC_PATHS.includes(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect logged in users away from "/" & "/login"
  if (sessionCookie && (pathname === "/" || pathname === "/login")) {
    const dashUrl = request.nextUrl.clone();
    dashUrl.pathname = "/dashboard";
    return NextResponse.redirect(dashUrl);
  }

  return NextResponse.next();
}

// ⚠️ Critical: Exclude ALL SSR runtime assets and API routes from middleware
export const config = {
  matcher: [
    "/((?!_next|static|favicon.ico|manifest|robots.txt|sitemap|api).*)",
  ],
};
