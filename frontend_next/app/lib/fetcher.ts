const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ||
  "http://127.0.0.1:8000";

function normalize(path: string) {
  if (!path.startsWith("/")) return `/${path}`;
  return path;
}

/**
 * Unified fetcher for backend API
 * Always hits FastAPI (never Next.js)
 */
export async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
) {
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const _path = normalize(endpoint);

  // ALWAYS hit backend
  const url = `${BACKEND_URL}${_path}`;

  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
    cache: "no-store",
  });
}
