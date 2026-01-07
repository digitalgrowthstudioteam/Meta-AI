import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Publicly accessible pages
const PUBLIC_PATHS = ["/", "/login"];

// 🔒 Admin emails (comma-separated in env)
const ADMIN_EMAILS = (process.env.NEXT_PUBLIC_ADMIN_EMAILS || "")
  .split(",")
  .map(e => e.trim().toLowerCase())
  .filter(Boolean);

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow Next.js internals & APIs
  if (pathname.startsWith("/_next") || pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  const session = request.cookies.get("meta_ai_session");

  // Not logged in → login
  if (!session) {
    if (PUBLIC_PATHS.includes(pathname)) {
      return NextResponse.next();
    }

    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const userIdentifier = session.value.toLowerCase();
  const isAdmin = ADMIN_EMAILS.includes(userIdentifier);

  // ✅ ADMIN: force landing to admin dashboard
  if (isAdmin && (pathname === "/" || pathname === "/dashboard")) {
    const adminUrl = request.nextUrl.clone();
    adminUrl.pathname = "/admin/dashboard";
    return NextResponse.redirect(adminUrl);
  }

  // ❌ Non-admin trying admin
  if (!isAdmin && pathname.startsWith("/admin")) {
    const userUrl = request.nextUrl.clone();
    userUrl.pathname = "/dashboard";
    return NextResponse.redirect(userUrl);
  }

  // Forward identity to backend
  const response = NextResponse.next();
  response.headers.set("X-User-Id", session.value);

  return response;
}

export const config = {
  matcher: ["/((?!_next|api|favicon.ico).*)"],
};
