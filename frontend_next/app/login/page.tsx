"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/fetcher";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await apiFetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ email }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }

      setSent(true);
      setCooldown(60);
    } catch (err: any) {
      console.error("Login error:", err);
      setError("Failed to send login link. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-sm border">
        <h1 className="text-2xl font-semibold text-slate-900">
          Digital Growth Studio
        </h1>

        <p className="mt-2 text-sm text-slate-600">
          Login using a secure magic link sent to your email.
        </p>

        {sent ? (
          <div className="mt-6 space-y-4">
            <div className="rounded-lg bg-green-50 p-4 text-sm text-green-700">
              ✅ Login link sent successfully.  
              Please check your inbox and spam folder.
            </div>

            <button
              onClick={() => {
                setSent(false);
                setError(null);
              }}
              disabled={cooldown > 0}
              className="w-full rounded-lg border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            >
              {cooldown > 0
                ? `Resend available in ${cooldown}s`
                : "Resend login link"}
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Email address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {error && (
              <div className="text-sm text-red-600">{error}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {loading ? "Sending link…" : "Send login link"}
            </button>
          </form>
        )}

        <p className="mt-6 text-xs text-slate-500">
          Secure, passwordless login via one-time email link.
        </p>
      </div>
    </div>
  );
}
