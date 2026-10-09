"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ShieldCheck, Search, Filter, Sparkles, Tag, Car } from "lucide-react";
import ReportModal from "@/components/report-modal";

export default function HomePage() {
  const [listings, setListings] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSeries, setSelectedSeries] = useState("ALL");
  const [loading, setLoading] = useState(true);

  // Default initial die-cast showcase if backend is offline during static render
  const initialItems = [
    {
      id: "demo-1",
      title: "Nissan Skyline GT-R R34 Car Culture - Mint Blister",
      series_name: "Car Culture",
      model_year: 2023,
      toy_code: "HKC34",
      condition: "MINT_CARD",
      tags: ["ORIGINAL", "SEALED"],
      price_rupees: 1450,
      verification_code: "CV-8R49K",
      media_url: "https://images.unsplash.com/photo-1581235720704-06d3acfcb36f?w=800",
      seller_name: "Arjun Diecast Garage",
      seller_tier: "TIER_1_VERIFIED"
    },
    {
      id: "demo-2",
      title: "'71 Datsun 510 Wagon Super Treasure Hunt",
      series_name: "Mainlines",
      model_year: 2022,
      toy_code: "HCW42",
      condition: "MINT_CARD",
      tags: ["ORIGINAL", "SEALED", "STH"],
      price_rupees: 4800,
      verification_code: "CV-2B91X",
      media_url: "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800",
      seller_name: "Mumbai Diecast Vault",
      seller_tier: "TIER_2_PRO"
    },
    {
      id: "demo-3",
      title: "Porsche 911 GT3 RS Boulevard Edition",
      series_name: "Boulevard",
      model_year: 2024,
      toy_code: "GJT68",
      condition: "MINT_CARD",
      tags: ["ORIGINAL", "SEALED"],
      price_rupees: 1100,
      verification_code: "CV-4P09M",
      media_url: "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800",
      seller_name: "Delhi Speed Club",
      seller_tier: "TIER_1_VERIFIED"
    }
  ];

  useEffect(() => {
    async function fetchListings() {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/listings");
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            setListings(data);
            setLoading(false);
            return;
          }
        }
      } catch (err) {
        // Fallback to demo items if local backend not running during build
      }
      setListings(initialItems);
      setLoading(false);
    }
    fetchListings();
  }, []);

  const filteredListings = listings.filter((item) => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          item.series_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeries = selectedSeries === "ALL" || item.series_name === selectedSeries;
    return matchesSearch && matchesSeries;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Hero Header */}
      <div className="rounded-2xl bg-gradient-to-r from-gray-900 via-gray-900 to-amber-950/40 border border-gray-800 p-8 mb-10 relative overflow-hidden shadow-2xl">
        <div className="max-w-2xl relative z-10">
          <div className="inline-flex items-center space-x-2 bg-amber-500/10 border border-amber-500/30 px-3 py-1 rounded-full text-amber-400 text-xs font-semibold mb-4">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>Escrow Protected &bull; Physical Code Verified</span>
          </div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight mb-3">
            Collect Authentic Die-Cast Cars with Zero Risk.
          </h1>
          <p className="text-gray-400 text-sm leading-relaxed mb-6">
            Every die-cast is physically reviewed by admin before release. Every payment is held in licensed escrow until you inspect delivery. Fake items mean a permanent device & bank ban.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/sell" className="bg-amber-500 hover:bg-amber-400 text-black font-bold px-5 py-2.5 rounded-lg text-sm transition shadow-lg shadow-amber-500/20">
              List a Car for Review
            </Link>
            <Link href="/rules" className="bg-gray-800 hover:bg-gray-700 text-white font-medium px-5 py-2.5 rounded-lg text-sm border border-gray-700 transition">
              Read Anti-Fraud Rules
            </Link>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-4 mb-8 justify-between items-center">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-500" />
          <input
            type="text"
            placeholder="Search Skyline, Boulevard, Car Culture..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-9 pr-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-amber-500 transition"
          />
        </div>

        <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
          {["ALL", "Car Culture", "Boulevard", "Mainlines"].map((series) => (
            <button
              key={series}
              onClick={() => setSelectedSeries(series)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                selectedSeries === series
                  ? "bg-amber-500 text-black"
                  : "bg-gray-900 text-gray-400 hover:text-white border border-gray-800"
              }`}
            >
              {series}
            </button>
          ))}
        </div>
      </div>

      {/* Marketplace Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredListings.map((item) => (
          <div
            key={item.id}
            className="bg-gray-900/90 border border-gray-800 rounded-xl overflow-hidden hover:border-amber-500/50 transition flex flex-col group"
          >
            {/* Image Preview with Physical Verification Badge */}
            <div className="relative h-56 bg-gray-950 overflow-hidden">
              <img
                src={item.media?.[0]?.media_url || item.media_url || "https://images.unsplash.com/photo-1581235720704-06d3acfcb36f?w=800"}
                alt={item.title}
                className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
              />
              <div className="absolute top-3 left-3 bg-black/75 backdrop-blur border border-amber-400/40 text-amber-300 px-2 py-0.5 rounded text-[11px] font-mono font-semibold flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                <span>CODE: {item.verification_code}</span>
              </div>
              <div className="absolute bottom-3 right-3 bg-emerald-950/80 border border-emerald-500/50 text-emerald-400 px-2 py-0.5 rounded text-[11px] font-bold">
                {item.condition?.replace("_", " ")}
              </div>
            </div>

            {/* Details Card */}
            <div className="p-5 flex-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 text-[11px] font-semibold text-gray-400 mb-1">
                  <span>{item.series_name}</span>
                  <span>&bull;</span>
                  <span>{item.model_year}</span>
                  {item.toy_code && (
                    <>
                      <span>&bull;</span>
                      <span className="font-mono bg-gray-800 px-1 rounded text-gray-300">{item.toy_code}</span>
                    </>
                  )}
                </div>
                <h3 className="font-bold text-white text-base leading-snug mb-2 group-hover:text-amber-400 transition">
                  {item.title}
                </h3>
              </div>

              <div className="pt-4 border-t border-gray-800 flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase font-bold text-gray-500 block">Escrow Price</span>
                  <span className="text-xl font-black text-amber-400">
                    ₹{item.price_rupees?.toLocaleString("en-IN") || (item.price_paise / 100).toLocaleString("en-IN")}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <ReportModal
                    targetType="LISTING"
                    targetId={item.id}
                    targetName={item.title}
                  />
                  <Link
                    href={`/listings/${item.id}`}
                    className="bg-gray-800 hover:bg-amber-500 hover:text-black text-gray-200 font-semibold px-4 py-2 rounded-lg text-xs transition"
                  >
                    Inspect & Buy
                  </Link>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
