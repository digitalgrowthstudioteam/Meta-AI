// ========================================================
// BASE_URL RESOLUTION (SSR + BROWSER SAFE)
// ========================================================
//
// NEXT_PUBLIC_BACKEND_URL is embedded by Next.js at build time.
// No window runtime overrides needed.
//
const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";

// ========================================================
// HELPERS
// ========================================================

// Always ensure leading slash
function ensureLeadingSlash(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

// Extract session token from cookie (browser only)
function getSessionToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)meta_ai_session=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

// ========================================================
// PUBLIC FETCHER (UNAUTHENTICATED)
// ========================================================
export const fetcher = async (path: string) => {
  const url = `${BASE_URL}${ensureLeadingSlash(path)}`;
  const res = await fetch(url, {
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error(`Fetch failed: ${res.status} ${url}`);
  }

  return res.json();
};

// ========================================================
// AUTHENTICATED FETCHER (AUTO TOKEN + COOKIES)
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

// ========================================================
// GET / POST HELPERS
// ========================================================
export const apiGet = async <T = any>(endpoint: string): Promise<T> => {
  const res = await apiFetch(endpoint, { method: "GET" });
  if (!res.ok) {
    throw new Error(`GET ${endpoint} failed: ${res.status}`);
  }
  return res.json();
};

export const apiPost = async <T = any>(endpoint: string, body: any): Promise<T> => {
  const headers = { "Content-Type": "application/json" };
  const res = await apiFetch(endpoint, {
    method: "POST",
    body: JSON.stringify(body),
    headers,
  });

  if (!res.ok) {
    throw new Error(`POST ${endpoint} failed: ${res.status}`);
  }

  return res.json();
};
