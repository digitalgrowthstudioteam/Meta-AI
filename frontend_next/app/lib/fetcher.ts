// app/lib/fetcher.ts

const BACKEND_URL =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_BACKEND_URL || ""
    : process.env.NEXT_PUBLIC_BACKEND_BROWSER_URL || "";

/**
 * Normalizes endpoint paths without stripping /api
 */
function normalize(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}

/**
 * Main API fetch wrapper with cookies enabled
 */
export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {});

  // Auto JSON header unless FormData
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const url = `${BACKEND_URL}${normalize(endpoint)}`;

  return fetch(url, {
    ...options,
    headers,
    credentials: "include", // required for session auth
  });
}

/**
 * Lightweight GET helper
 */
export async function apiGet<T = any>(endpoint: string): Promise<T> {
  const res = await apiFetch(endpoint, { method: "GET" });
  if (!res.ok) {
    throw new Error(`GET ${endpoint} failed: ${res.status}`);
  }
  return res.json();
}

/**
 * JSON POST helper
 */
export async function apiPost<T = any>(endpoint: string, body: any): Promise<T> {
  const res = await apiFetch(endpoint, {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST ${endpoint} failed: ${res.status}`);
  }
  return res.json();
}
