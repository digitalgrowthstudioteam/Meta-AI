// frontend_next/lib/fetcher.ts

// ========================================================
// BASE_URL RESOLUTION (WORKS IN SSR + BROWSER)
// ========================================================
//
// - NEXT_PUBLIC_BACKEND_URL is embedded at build time by Next.js
// - No window hacks needed
// - No runtime override needed
//
const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";

// ========================================================
// HELPERS
// ========================================================

// 🔒 Always ensure leading slash
function ensureLeadingSlash(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

// 🔒 Browser-only cookie token extractor
function getSessionToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)meta_ai_session=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

// ========================================================
// PUBLIC FETCHER (NO AUTH)
// ========================================================
export const fetcher = async (path: string) => {
  const url = `${BASE_URL}${ensureLeadingSlash(path)}`;
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) throw new Error(`Fetch failed: ${res.status} ${url}`);
  return res.json();
};

// ========================================================
// AUTHENTICATED FETCHER
// ========================================================
export const apiFetch = async (path: string, options: RequestInit = {}) => {
  const token = getSessionToken();

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${BASE_URL}${ensureLeadingSlash(path)}`;
  const res = await fetch(url, {
    credentials: "include",
    ...options,
    headers,
  });

  return res;
};
