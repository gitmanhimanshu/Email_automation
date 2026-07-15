"use client";

import { useEffect, useState } from "react";
import { Monitor, Moon, Sun } from "lucide-react";

type Theme = "light" | "dark" | "system";

const options: { value: Theme; icon: typeof Sun; label: string }[] = [
  { value: "light", icon: Sun, label: "Light" },
  { value: "dark", icon: Moon, label: "Dark" },
  { value: "system", icon: Monitor, label: "System" },
];

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("system");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setTheme((localStorage.getItem("theme") as Theme) ?? "system");
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const root = document.documentElement;
    if (theme === "system") {
      root.removeAttribute("data-theme");
      localStorage.removeItem("theme");
    } else {
      root.setAttribute("data-theme", theme);
      localStorage.setItem("theme", theme);
    }
  }, [theme, mounted]);

  // Render the shell during SSR so the nav doesn't shift when it hydrates.
  if (!mounted) return <div className="w-[86px] h-8" aria-hidden="true" />;

  return (
    <div
      className="flex items-center gap-0.5 p-0.5 rounded-full border border-[var(--border)] bg-[var(--surface)]"
      role="radiogroup"
      aria-label="Color theme"
    >
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          role="radio"
          aria-checked={theme === value}
          aria-label={label}
          onClick={() => setTheme(value)}
          className={`grid place-items-center w-7 h-7 rounded-full transition-colors ${
            theme === value
              ? "bg-[var(--surface-2)] text-[var(--text-primary)]"
              : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
          }`}
        >
          <Icon size={13} strokeWidth={2} />
        </button>
      ))}
    </div>
  );
}
