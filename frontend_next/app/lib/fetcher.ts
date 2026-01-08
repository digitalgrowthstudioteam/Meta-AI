export async function apiFetch(url: string, options: RequestInit = {}) {
  const impersonate = sessionStorage.getItem("impersonate_user");

  const headers = new Headers(options.headers || {});

  if (impersonate) {
    headers.set("X-Impersonate-User", impersonate);
  }

  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
}
