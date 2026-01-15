// frontend_next/lib/fetcher.ts

const BASE_URL =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_BACKEND_URL
    : (window as any).__NEXT_PUBLIC_BACKEND_URL ||
      process.env.NEXT_PUBLIC_BACKEND_URL;

if (typeof window !== "undefined") {
  (window as any).__NEXT_PUBLIC_BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
}

export const fetcher = (path: string) =>
  fetch(`${BASE_URL}${path}`).then((res) => res.json());

// Helper for authenticated requests
export const apiFetch = async (path: string, options: RequestInit = {}) => {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    ...options,
  });

  return res;
};
