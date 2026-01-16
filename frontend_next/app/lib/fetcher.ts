const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ||
  "http://127.0.0.1:8000";

function normalize(path: string) {
  if (!path.startsWith("/")) return `/${path}`;
  return path;
}

export async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
) {
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const _path = normalize(endpoint);

  // If endpoint already starts with `/api/`, call backend as-is
  // Fixes double-prefix `/api/api/...`
  const url = _path.startsWith("/api/")
    ? `${BACKEND_URL}${_path.replace(/^\/api/, "")}`
    : `${BACKEND_URL}${_path}`;

  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
}
