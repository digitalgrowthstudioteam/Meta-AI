import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// =============================================
// AUTH GUARD MIDDLEWARE (LOCKED)
// - Forces login for all app pages
// - Allows public access only to landing + login
// =============================================

const PUBLIC_PATHS = ["/", "/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public pages
  if (PUBLIC_PATHS.includes(pathname)) {
    return NextResponse.next();
  }

  // Allow Next.js internals
  if (pathname.startsWith("/_next") || pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  const session = request.cookies.get("meta_ai_session");

  // Not logged in → redirect to login
  if (!session) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/:path*"],
};
