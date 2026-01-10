import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/verify"];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Always allow Next.js internals, APIs, and static assets
  // (The config matcher handles most of this, but this is a safety check)
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/static") ||
    pathname.includes(".") // Files like favicon.ico, robots.txt
  ) {
    return NextResponse.next();
  }

  const session = request.cookies.get("meta_ai_session")?.value;

  // 2. Protect Private Routes
  // If user is NOT logged in AND trying to access a protected page
  if (!session && !PUBLIC_PATHS.includes(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 3. Redirect Logged-In Users away from Login/Public pages
  // If user IS logged in AND tries to visit login, send them to dashboard
  if (session && pathname === "/login") {
    const dashboardUrl = request.nextUrl.clone();
    dashboardUrl.pathname = "/dashboard";
    return NextResponse.redirect(dashboardUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Match all request paths except for the ones starting with:
  // - api (API routes)
  // - _next/static (static files)
  // - _next/image (image optimization files)
  // - favicon.ico (favicon file)
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
