import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Publicly accessible pages
const PUBLIC_PATHS = ["/", "/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow Next.js internals & APIs
  if (pathname.startsWith("/_next") || pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  const session = request.cookies.get("meta_ai_session");

  // Not logged in → redirect to login
  if (!session) {
    if (PUBLIC_PATHS.includes(pathname)) {
      return NextResponse.next();
    }

    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  /**
   * 🔒 IMPORTANT
   * Do NOT detect admin here.
   * meta_ai_session is a session token, not email.
   * Admin routing is handled after /api/session/context.
   */

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|api|favicon.ico).*)"],
};
