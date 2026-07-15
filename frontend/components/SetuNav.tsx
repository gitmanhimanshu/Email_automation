"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Waypoints } from "lucide-react";

export default function SetuNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? "pt-4 px-4" : "p-6"
      }`}
    >
      <div
        className={`mx-auto flex items-center justify-between max-w-7xl transition-all duration-300 ${
          scrolled
            ? "glass-panel rounded-2xl px-6 py-3 shadow-sm border border-gray-200/50 dark:border-gray-800/50 bg-white/70 dark:bg-gray-900/70 backdrop-blur-md"
            : "px-2 bg-transparent"
        }`}
      >
        <Link href="/" className="flex items-center gap-2 group">
          <div className="bg-gradient-to-br from-blue-600 to-indigo-600 p-1.5 rounded-lg text-white shadow-md shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-shadow">
            <Waypoints size={20} strokeWidth={2.5} />
          </div>
          <span className="font-hindi text-xl font-bold tracking-wide text-gray-900 dark:text-white">
            सेतु
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {["Features", "How It Works", "Pricing", "Resources", "About"].map((item) => (
            <Link
              key={item}
              href={`#${item.toLowerCase().replace(/\s+/g, "-")}`}
              className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors"
            >
              {item}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="hidden sm:block text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors"
          >
            Login
          </Link>
          <Link
            href="/start"
            className="text-sm font-medium bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 dark:text-gray-900 text-white px-5 py-2 rounded-full transition-all active:scale-95 shadow-sm hover:shadow-md"
          >
            Get Started
          </Link>
        </div>
      </div>
    </motion.header>
  );
}
