const BACKEND_URL =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_BACKEND_URL
    : process.env.NEXT_PUBLIC_BACKEND_BROWSER_URL;

function normalize(path: string) {
  let p = path.startsWith("/") ? path : `/${path}`;
  if (p.startsWith("/api/")) p = p.replace("/api/", "/");
  if (p === "/api") p = "/";
  return p;
}

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const url = `${BACKEND_URL}${normalize(endpoint)}`;

  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
}
