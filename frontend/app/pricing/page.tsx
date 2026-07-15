import Link from "next/link";
import type { Metadata } from "next";
import { Check } from "lucide-react";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Start for free, upgrade when you need more volume.",
};

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect for testing the waters and sending your first few applications.",
    features: [
      "5 successful emails total",
      "Send from your Gmail",
      "Full AI email generation",
      "Resume link appending",
      "Duplicate send prevention",
    ],
    button: "Get started",
    href: "/docs",
    primary: false,
  },
  {
    name: "Pro",
    price: "$9",
    period: "per month",
    description: "For serious job seekers. Currently manual upgrade only (Payment gateway coming soon).",
    features: [
      "Unlimited emails (up to Gmail limits)",
      "Send from your Gmail",
      "Full AI email generation",
      "Duplicate send prevention",
      "Paced sending for deliverability",
      "Priority email support",
    ],
    button: "Contact to Upgrade",
    href: "mailto:himanshuyada70@gmail.com?subject=Setu Pro Upgrade",
    primary: true,
  },
];

export default function Pricing() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-20 sm:py-32">
      <div className="text-center max-w-3xl mx-auto">
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight">
          Simple, transparent pricing
        </h1>
        <p className="mt-6 text-lg text-[var(--text-secondary)] leading-relaxed">
          Setu is free for your first 5 successful emails. After that, upgrade to
          send as many as your Gmail account allows. No hidden fees, no credit
          card required to start.
        </p>
      </div>

      <div className="mt-20 grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`relative flex flex-col rounded-3xl border p-8 shadow-sm ${
              plan.primary
                ? "border-[var(--accent)] bg-[var(--surface)] ring-1 ring-[var(--accent)]"
                : "border-[var(--border)] bg-[var(--plane)]"
            }`}
          >
            {plan.primary && (
              <div className="absolute -top-3 left-0 right-0 mx-auto w-max rounded-full bg-[var(--accent)] px-3 py-1 text-xs font-semibold text-white">
                Most popular
              </div>
            )}

            <div className="mb-6">
              <h2 className="text-xl font-semibold">{plan.name}</h2>
              <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
                {plan.description}
              </p>
            </div>

            <div className="mb-8">
              <span className="text-4xl font-bold tracking-tight">{plan.price}</span>
              <span className="text-sm font-medium text-[var(--text-muted)] ml-2">
                /{plan.period}
              </span>
            </div>

            <ul className="mb-8 space-y-4 flex-1">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-sm">
                  <Check
                    size={18}
                    className="shrink-0 text-[var(--accent)] mt-0.5"
                    strokeWidth={2.5}
                  />
                  <span className="text-[var(--text-secondary)] leading-relaxed">
                    {feature}
                  </span>
                </li>
              ))}
            </ul>

            <Link
              href={plan.href}
              className={`block w-full rounded-xl py-3 px-4 text-center text-sm font-medium transition-all ${
                plan.primary
                  ? "bg-[var(--accent)] text-white hover:opacity-90 shadow-md shadow-[var(--accent-glow)]"
                  : "bg-[var(--surface-2)] text-[var(--text-primary)] hover:bg-[var(--border)]"
              }`}
            >
              {plan.button}
            </Link>
            {plan.primary && (
              <div className="mt-4 text-xs text-center text-[var(--text-secondary)] space-y-1">
                <p>or call/WhatsApp: <strong>+91 7080159181</strong></p>
                <p>email: <strong>himanshuyada70@gmail.com</strong></p>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-24 max-w-3xl mx-auto text-center">
        <h2 className="text-2xl font-semibold tracking-tight">Frequently asked questions</h2>
        <div className="mt-8 grid sm:grid-cols-2 gap-8 text-left">
          <div>
            <h3 className="font-semibold text-sm">What counts as a "free email"?</h3>
            <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
              Only emails that are successfully handed off to Gmail and sent. Bounces or failures do not count against your 5 free emails.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-sm">Can I cancel anytime?</h3>
            <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
              Yes, if you upgrade to Pro, you can cancel your subscription at any time from the dashboard. You will retain access until the end of your billing period.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-sm">Why is there a limit on Pro?</h3>
            <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
              Setu does not impose its own limits on the Pro plan, but Google restricts how many emails a standard Gmail account can send per day to prevent spam. We automatically pace your sends to keep your account safe.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-sm">Is my data secure?</h3>
            <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
              100%. We never read your inbox, and we do not store your Google password or tokens. You can revoke Setu's access from your Google account settings at any time.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
