import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Publicly accessible pages
const PUBLIC_PATHS = ["/", "/login"];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow Next.js internals, static files & APIs
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/favicon.ico")
  ) {
    return NextResponse.next();
  }

  const session = request.cookies.get("meta_ai_session")?.value;

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

  // Admin-only paths
  if (pathname.startsWith("/admin")) {
    try {
      const backendURL = `${process.env.NEXT_PUBLIC_BACKEND_URL}/session/context`;
      const res = await fetch(backendURL, {
        method: "GET",
        headers: {
          cookie: `meta_ai_session=${session}`,
        },
        cache: "no-store",
      });

      if (!res.ok) {
        const loginUrl = request.nextUrl.clone();
        loginUrl.pathname = "/login";
        loginUrl.searchParams.set("next", pathname);
        return NextResponse.redirect(loginUrl);
      }

      const data = await res.json();

      if (!data?.user?.is_admin) {
        const deniedUrl = request.nextUrl.clone();
        deniedUrl.pathname = "/dashboard";
        return NextResponse.redirect(deniedUrl);
      }
    } catch {
      const loginUrl = request.nextUrl.clone();
      loginUrl.pathname = "/login";
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|api|favicon.ico).*)"],
};
