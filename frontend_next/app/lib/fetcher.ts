const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const impersonate =
    typeof window !== "undefined"
      ? sessionStorage.getItem("impersonate_user")
      : null;

  const headers = new Headers(options.headers || {});

  if (impersonate) {
    headers.set("X-Impersonate-User", impersonate);
  }

  // Default to JSON if not FormData
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // 🔒 CRITICAL FIX:
  // /api/* → Next.js
  // everything else → backend
  const url = endpoint.startsWith("/api/")
    ? endpoint
    : endpoint.startsWith("http")
    ? endpoint
    : `${BACKEND_URL}${endpoint}`;

  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
}
