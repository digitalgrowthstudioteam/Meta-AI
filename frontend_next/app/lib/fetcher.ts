const BACKEND_URL =
  (typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_BACKEND_URL
    : process.env.NEXT_PUBLIC_BACKEND_BROWSER_URL) ||
  "https://meta-ai.digitalgrowthstudio.in";

function normalize(path: string) {
  if (!path.startsWith("/")) return `/${path}`;
  return path;
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
    cache: "no-store",
  });
}
