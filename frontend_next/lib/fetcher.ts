// frontend_next/lib/fetcher.ts
export const fetcher = (url: string) => fetch(url).then((res) => res.json());

// Helper for authenticated requests if needed later
export const apiFetch = async (url: string, options: RequestInit = {}) => {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error('API Error');
  return res;
};
