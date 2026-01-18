const BASE_URL =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_BACKEND_URL
    : (window as any).__NEXT_PUBLIC_BACKEND_URL ||
      process.env.NEXT_PUBLIC_BACKEND_URL;

if (typeof window !== "undefined") {
  (window as any).__NEXT_PUBLIC_BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
}

// 🔒 Force leading slash always
function ensureLeadingSlash(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

// 🔒 Extract session token from cookie
function getSessionToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)meta_ai_session=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

// Public fetcher (no auth)
export const fetcher = (path: string) =>
  fetch(`${BASE_URL}${ensureLeadingSlash(path)}`).then((res) => res.json());

// Authenticated fetcher
export const apiFetch = async (path: string, options: RequestInit = {}) => {
  const token = getSessionToken();

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${BASE_URL}${ensureLeadingSlash(path)}`, {
    credentials: "include",
    ...options,
    headers,
  });

  return res;
};
