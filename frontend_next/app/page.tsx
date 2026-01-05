"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle, Sparkles, Shield, BarChart3, Brain } from "lucide-react";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-amber-50 to-white text-gray-900">
      {/* HERO */}
      <section className="max-w-7xl mx-auto px-6 pt-24 pb-20 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 text-amber-800 text-sm mb-6">
            <Sparkles size={16} /> AI‑Powered Meta Ads Optimization
          </div>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Digital Growth Studio
          </h1>
          <p className="mt-4 text-lg text-gray-600 max-w-xl">
            Read‑only, explainable AI that tells you exactly what is working in your Meta Ads — creatives, audiences, placements, cities, age groups, and more.
          </p>

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
        </div>

        <div className="relative">
          <div className="rounded-2xl bg-white shadow-xl border border-amber-100 p-6">
            <ul className="space-y-4">
              {["Creative‑level performance", "Placement & audience insights", "City, gender & age breakdowns", "AI‑generated optimization actions", "No campaign edits — 100% safe"].map((item) => (
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
          <div>
            <Shield className="mx-auto text-indigo-600" size={28} />
            <h3 className="font-semibold mt-2">Read‑Only & Safe</h3>
            <p className="text-sm text-gray-600 mt-1">We never change your ads. AI only suggests.</p>
          </div>
          <div>
            <Brain className="mx-auto text-indigo-600" size={28} />
            <h3 className="font-semibold mt-2">Explainable AI</h3>
            <p className="text-sm text-gray-600 mt-1">Every suggestion comes with reasoning.</p>
          </div>
          <div>
            <BarChart3 className="mx-auto text-indigo-600" size={28} />
            <h3 className="font-semibold mt-2">Deep Performance Insights</h3>
            <p className="text-sm text-gray-600 mt-1">Know exactly what is driving results.</p>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold text-center">What You Get</h2>
        <p className="text-center text-gray-600 mt-3 max-w-2xl mx-auto">
          Built for founders, marketers, and performance teams who want clarity — not guesswork.
        </p>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          {[{
            title: "Campaign Visibility",
            desc: "See all Meta campaigns with AI‑active tagging and health indicators."
          }, {
            title: "Creative Intelligence",
            desc: "Identify winning creatives and fatigue signals automatically."
          }, {
            title: "Audience Insights",
            desc: "Breakdowns by city, gender, age group, and placement."
          }, {
            title: "AI Actions",
            desc: "Clear, human‑readable suggestions ranked by impact."
          }, {
            title: "Industry Benchmarks",
            desc: "Compare your performance with industry standards."
          }, {
            title: "Zero Risk",
            desc: "No write access to Meta. Nothing can break your ads."
          }].map((f) => (
            <div key={f.title} className="rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition">
              <h3 className="font-semibold text-lg">{f.title}</h3>
              <p className="text-gray-600 mt-2 text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-20 text-center">
          <h2 className="text-3xl font-bold">Start Your Free Trial</h2>
          <p className="mt-3 text-indigo-100 max-w-xl mx-auto">
            Connect your Meta Ads account and see AI insights in minutes.
            No credit card. No risk.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 mt-8 rounded-xl bg-white px-8 py-4 text-indigo-600 font-semibold hover:bg-gray-100 transition"
          >
            Get Started <ArrowRight size={18} />
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
