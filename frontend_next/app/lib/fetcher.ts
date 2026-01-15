const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ||
  "http://127.0.0.1:8000";

/**
 * Ensure a leading slash, no double-slash
 */
function normalize(path: string) {
  if (!path.startsWith("/")) return `/${path}`;
  return path;
}

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const impersonate =
    typeof window !== "undefined"
      ? sessionStorage.getItem("impersonate_user")
      : null;

  const headers = new Headers(options.headers || {});

  if (impersonate) {
    headers.set("X-Impersonate-User", impersonate);
  }

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const _path = normalize(endpoint);

  /**
   * RULES:
   * /api/*         → Next.js internal API
   * /backend/*     → Maps to backend, strips /backend
   * everything else → calls backend
   */
  const url = _path.startsWith("/api/")
    ? _path // Next.js API
    : `${BACKEND_URL}${_path}`; // Backend API

  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
}
