"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle, Sparkles, Shield, BarChart3, Brain, Lock } from "lucide-react";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-amber-50 to-white text-gray-900">
      {/* HERO */}
      <section className="max-w-7xl mx-auto px-6 pt-20 pb-16 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 text-amber-800 text-sm mb-6">
            <Sparkles size={16} /> Read‑Only AI for Meta Ads
          </div>

          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            See What’s Really Working in Your Meta Ads
          </h1>

          <p className="mt-4 text-lg text-gray-600 max-w-xl">
            Digital Growth Studio gives you clear, explainable AI insights across creatives, audiences, placements, cities, age groups — without touching your campaigns.
          </p>

          <ul className="mt-6 space-y-2 text-sm text-gray-700">
            {["No write access to Meta", "Explainable AI decisions", "Campaign‑level & creative‑level clarity", "Built for scale & safety"].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <CheckCircle className="text-green-600 mt-0.5" size={16} />
                <span>{item}</span>
              </li>
            ))}
          </ul>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-white font-medium hover:bg-indigo-700 transition"
            >
              Start Free Trial <ArrowRight size={18} />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center gap-2 rounded-xl border border-gray-300 px-6 py-3 font-medium hover:bg-gray-100 transition"
            >
              Explore Features
            </a>
          </div>

          <div className="mt-6 flex items-center gap-2 text-xs text-gray-500">
            <Lock size={14} /> Secure magic‑link login · No credit card required
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="relative">
          <div className="rounded-2xl bg-white shadow-xl border border-amber-100 p-6">
            <ul className="space-y-4">
              {[
                "Creative‑level performance",
                "Audience & placement breakdowns",
                "City, gender & age insights",
                "AI‑generated optimization actions",
                "100% read‑only & safe",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <CheckCircle className="text-green-600 mt-1" size={20} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* TRUST STRIP */}
      <section className="bg-white border-t border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-10 grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
          <TrustItem icon={<Shield size={28} />} title="Read‑Only & Safe" desc="We never change your ads." />
          <TrustItem icon={<Brain size={28} />} title="Explainable AI" desc="Every insight shows why." />
          <TrustItem icon={<BarChart3 size={28} />} title="Deep Insights" desc="Creative to city‑level clarity." />
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold text-center">What You Get</h2>
        <p className="text-center text-gray-600 mt-3 max-w-2xl mx-auto">
          Everything you need to understand performance — without risk or guesswork.
        </p>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          {["Campaign Visibility", "Creative Intelligence", "Audience Insights", "AI Actions", "Benchmarks", "Zero Risk"].map((title) => (
            <div key={title} className="rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition">
              <h3 className="font-semibold text-lg">{title}</h3>
              <p className="text-gray-600 mt-2 text-sm">
                Designed for real‑world Meta Ads teams.
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="bg-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-20 text-center">
          <h2 className="text-3xl font-bold">Try Digital Growth Studio Free</h2>
          <p className="mt-3 text-indigo-100 max-w-xl mx-auto">
            Connect Meta Ads · See insights in minutes · Cancel anytime
          </p>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 mt-8 rounded-xl bg-white px-8 py-4 text-indigo-600 font-semibold hover:bg-gray-100 transition"
          >
            Start Free Trial <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-white border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-sm text-gray-500">© {new Date().getFullYear()} Digital Growth Studio</div>
          <div className="flex gap-4 text-sm">
            <Link href="/login" className="hover:underline">Login</Link>
            <a href="#features" className="hover:underline">Features</a>
          </div>
        </div>
      </footer>
    </main>
  );
}

function TrustItem({ icon, title, desc }: { icon: any; title: string; desc: string }) {
  return (
    <div>
      <div className="mx-auto text-indigo-600">{icon}</div>
      <h3 className="font-semibold mt-2">{title}</h3>
      <p className="text-sm text-gray-600 mt-1">{desc}</p>
    </div>
  );
}
