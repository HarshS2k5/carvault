import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { ShieldCheck, PlusCircle, LayoutDashboard, FileText, Sparkles, Scale, AlertOctagon, ShieldAlert } from "lucide-react";

export const metadata: Metadata = {
  title: "CarVault | Trust-First Die-Cast Marketplace India",
  description: "India's premier verified die-cast collectible marketplace. Every listing verified by experts. Every payment held in escrow until delivery.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex flex-col min-h-screen">
        {/* Trust Banner */}
        <div className="bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-600 text-black text-xs font-semibold py-1.5 px-4 text-center tracking-wide">
          🛡️ CARVAULT GUARANTEE: 100% Admin Reviewed Listings &bull; Zero Direct Transfers &bull; Escrow Protected Payouts
        </div>

        {/* Global Navigation Header */}
        <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center font-black text-black text-lg shadow-md shadow-amber-500/20">
                CV
              </span>
              <span className="font-extrabold text-xl tracking-tight text-white">
                CAR<span className="text-amber-400">VAULT</span>
              </span>
              <span className="text-[10px] font-bold uppercase bg-amber-400/10 text-amber-400 border border-amber-400/30 px-1.5 py-0.5 rounded">
                India MVP
              </span>
            </Link>

            <nav className="flex items-center space-x-6 text-sm font-medium">
              <Link href="/" className="text-gray-300 hover:text-white transition">
                Browse Marketplace
              </Link>
              <Link href="/sell" className="flex items-center space-x-1 text-amber-400 hover:text-amber-300 font-semibold transition">
                <PlusCircle className="w-4 h-4" />
                <span>Sell a Car</span>
              </Link>
              <Link href="/admin/review" className="flex items-center space-x-1 text-gray-300 hover:text-amber-400 transition">
                <LayoutDashboard className="w-4 h-4" />
                <span>Review</span>
              </Link>
              <Link href="/admin/disputes" className="flex items-center space-x-1 text-gray-300 hover:text-amber-400 transition">
                <AlertOctagon className="w-4 h-4" />
                <span>Disputes</span>
              </Link>
              <Link href="/admin/reports" className="flex items-center space-x-1 text-gray-300 hover:text-amber-400 transition">
                <ShieldAlert className="w-4 h-4" />
                <span>Reports</span>
              </Link>
              <Link href="/admin/finance" className="flex items-center space-x-1 text-gray-300 hover:text-amber-400 transition">
                <Scale className="w-4 h-4" />
                <span>Finance</span>
              </Link>
              <Link href="/rules" className="flex items-center space-x-1 text-gray-400 hover:text-gray-200 transition">
                <FileText className="w-4 h-4" />
                <span>Rules & Safety</span>
              </Link>
            </nav>
          </div>
        </header>

        {/* Main Viewport */}
        <main className="flex-1">{children}</main>

        {/* Compliance & Regulatory Footer */}
        <footer className="border-t border-gray-800 bg-gray-950 text-gray-400 text-xs py-8">
          <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
              <p className="font-semibold text-gray-300">CarVault Collectibles Marketplace Private Limited</p>
              <p className="text-gray-500 mt-1">Regulated intermediary under Consumer Protection (E-Commerce) Rules 2020 & IT Rules 2021.</p>
              <p className="text-gray-500">Payments routed strictly through RBI-authorized Payment Aggregator Escrow nodes.</p>
            </div>
            <div className="flex space-x-6 text-gray-400">
              <Link href="/rules" className="hover:text-amber-400 transition">Grievance Officer</Link>
              <Link href="/rules#prohibited" className="hover:text-amber-400 transition">Anti-Fraud Policy</Link>
              <Link href="/rules#ladder" className="hover:text-amber-400 transition">Penalty Ladder</Link>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
