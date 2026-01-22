import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/verify"];
const WEBHOOK_PATHS = ["/billing/webhook"];

// Pages allowed when trial expired
const TRIAL_ALLOWED = ["/billing", "/logout"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 🔓 Allow webhook paths through without auth
  if (WEBHOOK_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // System/static/assets bypass
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
  const trialCookie = request.cookies.get("meta_ai_trial_status")?.value;
  const isTrialExpired = trialCookie === "expired";

  // =====================================================
  // 🔒 ADMIN PROTECTION
  // =====================================================
  if (pathname.startsWith("/admin")) {
    if (!sessionCookie) {
      const loginUrl = request.nextUrl.clone();
      loginUrl.pathname = "/login";
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }

    // First load → allow context to set role cookie
    if (!roleCookie) return NextResponse.next();

    if (roleCookie !== "admin") {
      const dashUrl = request.nextUrl.clone();
      dashUrl.pathname = "/dashboard";
      return NextResponse.redirect(dashUrl);
    }

    return NextResponse.next();
  }

  // =====================================================
  // 🔐 AUTH PROTECTION FOR USER
  // =====================================================
  if (!sessionCookie && !PUBLIC_PATHS.includes(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // =====================================================
  // 🎯 TRIAL ENFORCEMENT (PHASE-8)
  // =====================================================
  if (sessionCookie && isTrialExpired) {
    const allowed = TRIAL_ALLOWED.some((p) => pathname.startsWith(p));
    if (!allowed) {
      const billingUrl = request.nextUrl.clone();
      billingUrl.pathname = "/billing";
      billingUrl.searchParams.set("upgrade", "1");
      return NextResponse.redirect(billingUrl);
    }
  }

  // =====================================================
  // ↪️ POST-LOGIN REDIRECT
  // =====================================================
  if (sessionCookie && (pathname === "/" || pathname === "/login")) {
    const dashUrl = request.nextUrl.clone();
    dashUrl.pathname = "/dashboard";
    return NextResponse.redirect(dashUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next|static|favicon.ico|manifest|robots.txt|sitemap|api|billing/webhook).*)",
  ],
};
