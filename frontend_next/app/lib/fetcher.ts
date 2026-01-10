const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const impersonate = typeof window !== "undefined" ? sessionStorage.getItem("impersonate_user") : null;

  const headers = new Headers(options.headers || {});

  if (impersonate) {
    headers.set("X-Impersonate-User", impersonate);
  }

  // Default to JSON if not FormData
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Construct full URL if it's a relative path
  const url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint}`;

  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
}
