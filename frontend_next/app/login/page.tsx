"use client";

import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!email) return;

    setLoading(true);
    setError(null);

    try {
      const body = new URLSearchParams();
      body.append("email", email);

      const res = await fetch("https://meta-ai.digitalgrowthstudio.in/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
      });

      // ✅ ACCEPT 204 AS SUCCESS
      if (res.status !== 204) {
        throw new Error();
      }

      setSuccess(true);
    } catch {
      setError("Unable to send magic link. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg shadow-sm p-8">
        <div className="mb-6 text-center">
          <h1 className="text-xl font-semibold text-gray-900">
            Digital Growth Studio
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Sign in with your email to continue
          </p>
        </div>

        {success ? (
          <div className="text-center text-sm text-gray-700">
            <div className="mb-2 font-medium">
              Check your email 📩
            </div>
            <p className="text-gray-500">
              We’ve sent you a magic login link.
              <br />
              Click it to access your dashboard.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="you@company.com"
              />
            </div>

            {error && (
              <div className="text-sm text-red-600">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-blue-600 text-white py-2 text-sm font-medium hover:bg-blue-700 transition disabled:opacity-60"
            >
              {loading ? "Sending link…" : "Send Magic Link"}
            </button>
          </form>
        )}

        <div className="mt-6 text-center text-xs text-gray-400">
          Passwordless login • Secure • No spam
        </div>
      </div>
    </div>
  );
}
