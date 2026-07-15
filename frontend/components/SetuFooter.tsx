import Link from "next/link";
import { Waypoints } from "lucide-react";

export default function SetuFooter() {
  return (
    <footer className="border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 pt-20 pb-10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-10 lg:gap-8 mb-16">
          <div className="col-span-2 lg:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <div className="bg-gradient-to-br from-blue-600 to-indigo-600 p-1.5 rounded-lg text-white">
                <Waypoints size={20} strokeWidth={2.5} />
              </div>
              <span className="font-hindi text-2xl font-bold tracking-wide">सेतु</span>
            </Link>
            <p className="text-gray-500 dark:text-gray-400 font-hindi mb-6 max-w-xs">
              "एक मार्गदर्शक, आपके सपनों और अवसरों के बीच।"
            </p>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Product</h4>
            <ul className="space-y-3">
              {["Features", "Integrations", "Pricing", "Changelog"].map(link => (
                <li key={link}>
                  <Link href="#" className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors">{link}</Link>
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Resources</h4>
            <ul className="space-y-3">
              {["Documentation", "Blog", "Community", "Support"].map(link => (
                <li key={link}>
                  <Link href="#" className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors">{link}</Link>
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Company</h4>
            <ul className="space-y-3">
              {["About", "Careers", "Privacy Policy", "Terms of Service"].map(link => (
                <li key={link}>
                  <Link href="#" className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors">{link}</Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
        
        <div className="pt-8 border-t border-gray-200 dark:border-gray-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            © {new Date().getFullYear()} Setu Inc. All rights reserved.
          </p>
          <div className="flex gap-4">
            {["Twitter", "GitHub", "LinkedIn"].map(social => (
              <a key={social} href="#" className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors">
                {social}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
