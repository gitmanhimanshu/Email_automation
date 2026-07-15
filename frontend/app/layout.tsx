import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { AUTHOR, GITHUB_URL, SITE_URL } from "@/lib/site";

const description =
  "Setu is an AI-powered Model Context Protocol (MCP) server that lets Claude, ChatGPT, and Cursor automate job applications directly from your Gmail. 100% secure, send-only access.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Setu — Automate Job Applications with AI via Gmail MCP",
    template: "%s | Setu AI Assistant",
  },
  description,
  applicationName: "Setu",
  creator: AUTHOR.name,
  publisher: AUTHOR.name,
  authors: [{ name: AUTHOR.name, url: AUTHOR.github }],
  keywords: [
    "AI job application sender",
    "Automate job search with AI",
    "Send emails with Claude",
    "Claude MCP for Gmail",
    "ChatGPT MCP email sender",
    "AI Career Assistant",
    "Model Context Protocol",
    "MCP server",
    "Gmail API AI automation",
    "Cursor AI Gmail connector",
    "Automated resume sender",
  ],
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: "Setu",
    title: "Setu — connect AI to Gmail in minutes",
    description,
  },
  twitter: {
    card: "summary_large_image",
    title: "Setu — connect AI to Gmail in minutes",
    description,
  },
  robots: { index: true, follow: true },
  alternates: { canonical: SITE_URL },
};

/* JSON-LD describes only what's verifiable: the software, its license, and who
   wrote it. No invented ratings or review counts. */
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Setu",
  applicationCategory: "DeveloperApplication",
  operatingSystem: "Any",
  description,
  url: SITE_URL,
  codeRepository: GITHUB_URL,
  license: "https://opensource.org/licenses/MIT",
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD", description: "Free for first 5 emails" },
  author: {
    "@type": "Person",
    name: AUTHOR.name,
    url: AUTHOR.github,
    sameAs: [AUTHOR.github, AUTHOR.linkedin],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Applies the stored theme before first paint, so a dark-mode reader
            never gets a white flash on load. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t)}catch(e){}`,
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-screen antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-[var(--surface)] focus:border focus:border-[var(--border)]"
        >
          Skip to content
        </a>
        <Nav />
        <div id="main">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
