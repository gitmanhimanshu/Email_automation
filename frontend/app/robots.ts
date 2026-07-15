import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Nothing useful to a crawler, and it's per-user by definition.
      disallow: "/dashboard",
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
