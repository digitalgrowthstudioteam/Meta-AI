import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/verify"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow internal paths
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/static") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Session cookie
  const session = request.cookies.get("meta_ai_session")?.value;

  // ❗ Skip forcing `/login` → `/dashboard` redirect on admin panel paths
  const isAdminRoute = pathname.startsWith("/admin");

  // Unauthenticated
  if (!session && !PUBLIC_PATHS.includes(pathname) && !isAdminRoute) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Logged-in but on login/root → redirect only for non-admin pages
  if (session && !isAdminRoute && (pathname === "/" || pathname === "/login")) {
    const dashboard = request.nextUrl.clone();
    dashboard.pathname = "/dashboard";
    return NextResponse.redirect(dashboard);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
