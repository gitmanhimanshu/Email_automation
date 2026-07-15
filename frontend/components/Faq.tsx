"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { FAQS } from "@/lib/site";

export default function Faq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="divide-y divide-[var(--border)] border-y border-[var(--border)]">
      {FAQS.map((faq, i) => {
        const isOpen = open === i;
        return (
          <div key={faq.q}>
            <h3>
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                aria-expanded={isOpen}
                aria-controls={`faq-${i}`}
                className="w-full flex items-start justify-between gap-6 py-5 text-left group"
              >
                <span className="font-medium group-hover:text-[var(--accent)] transition-colors">
                  {faq.q}
                </span>
                <Plus
                  size={16}
                  className={`mt-0.5 shrink-0 text-[var(--text-muted)] transition-transform duration-200 ${
                    isOpen ? "rotate-45" : ""
                  }`}
                />
              </button>
            </h3>
            <div
              id={`faq-${i}`}
              hidden={!isOpen}
              className="pb-5 -mt-1 text-sm text-[var(--text-secondary)] leading-relaxed max-w-2xl"
            >
              {faq.a}
            </div>
          </div>
        );
      })}
    </div>
  );
}
