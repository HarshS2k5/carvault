"use client";

import { useState } from "react";
import { AlertOctagon, Video, ShieldCheck, CheckCircle2, ArrowRight, User, Package } from "lucide-react";

export default function AdminDisputesPage() {
  const [activeDispute, setActiveDispute] = useState({
    id: "disp-demo-01",
    order_id: "ord-892401",
    reason: "Delivered blister card has cracked bubble along the top edge, and card back is creased. Buyer submitted continuous unboxing video.",
    seller_name: "Arjun Diecast Garage",
    buyer_name: "Collector Rohit",
    escrow_amount_rupees: 1550,
    status: "UNDER_REVIEW",
    seller_packing_video: "https://media.carvault.in/seller_packing_proof.mp4",
    buyer_unboxing_video: "https://media.carvault.in/buyer_unboxing_proof.mp4",
  });

  const [adminNotes, setAdminNotes] = useState("");
  const [resolutionNotice, setResolutionNotice] = useState("");

  const handleResolve = (action: "RELEASE_TO_SELLER" | "REFUND_TO_BUYER") => {
    if (action === "RELEASE_TO_SELLER") {
      setActiveDispute({ ...activeDispute, status: "RESOLVED_RELEASED" });
      setResolutionNotice("✅ Dispute resolved in favor of SELLER. Escrow funds released to seller bank account.");
    } else {
      setActiveDispute({ ...activeDispute, status: "RESOLVED_REFUNDED" });
      setResolutionNotice("✅ Dispute resolved in favor of BUYER. Full refund issued to buyer.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center space-x-1.5 text-xs font-bold uppercase tracking-wider text-red-400 bg-red-400/10 px-2.5 py-1 rounded border border-red-400/20 mb-2">
          <AlertOctagon className="w-3.5 h-3.5" />
          <span>Escrow Dispute Arbitration</span>
        </div>
        <h1 className="text-2xl font-black text-white">Dispute Resolution Cockpit</h1>
        <p className="text-gray-400 text-xs mt-1">
          Arbitrate claims with continuous video evidence: compare seller pre-dispatch packing video against buyer unboxing video.
        </p>
      </div>

      {resolutionNotice && (
        <div className="p-4 rounded-xl text-xs font-bold bg-emerald-950/40 border border-emerald-500/40 text-emerald-300">
          {resolutionNotice}
        </div>
      )}

      {/* Case Overview */}
      <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-800 pb-4">
          <div>
            <h2 className="text-base font-bold text-white">
              Case #{activeDispute.id} &bull; Order #{activeDispute.order_id}
            </h2>
            <p className="text-xs text-gray-400 mt-1">
              Disputed Escrow Amount: <span className="font-bold text-amber-400 font-mono">₹{activeDispute.escrow_amount_rupees}</span>
            </p>
          </div>
          <span className="bg-amber-950 text-amber-400 text-xs font-bold px-3 py-1 rounded border border-amber-500/40">
            {activeDispute.status}
          </span>
        </div>
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Buyer's Claim Description:</h4>
          <p className="text-xs text-gray-300 leading-relaxed bg-gray-950 p-3 rounded-lg border border-gray-800">
            "{activeDispute.reason}"
          </p>
        </div>
      </div>

      {/* Side-by-Side Evidence Comparison View */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Seller Packing Video */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <div className="flex items-center space-x-2">
              <Package className="w-4 h-4 text-emerald-400" />
              <h3 className="font-bold text-sm text-white">Seller Pre-Dispatch Packing Video</h3>
            </div>
            <span className="text-[11px] text-gray-400">Seller: {activeDispute.seller_name}</span>
          </div>

          <div className="bg-black rounded-xl h-64 flex flex-col items-center justify-center border border-gray-800 p-4 text-center">
            <Video className="w-10 h-10 text-emerald-400 mb-2" />
            <span className="text-xs font-bold text-gray-300">Continuous Packing Stream</span>
            <span className="text-[11px] text-gray-500 font-mono mt-1">{activeDispute.seller_packing_video}</span>
            <span className="mt-3 text-[10px] bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30">
              Shows unbent card corners and Bubble Wrap
            </span>
          </div>
        </div>

        {/* Right: Buyer Unboxing Video */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <div className="flex items-center space-x-2">
              <User className="w-4 h-4 text-red-400" />
              <h3 className="font-bold text-sm text-white">Buyer Continuous Unboxing Video</h3>
            </div>
            <span className="text-[11px] text-gray-400">Buyer: {activeDispute.buyer_name}</span>
          </div>

          <div className="bg-black rounded-xl h-64 flex flex-col items-center justify-center border border-gray-800 p-4 text-center">
            <Video className="w-10 h-10 text-red-400 mb-2" />
            <span className="text-xs font-bold text-gray-300">Continuous Unboxing Stream</span>
            <span className="text-[11px] text-gray-500 font-mono mt-1">{activeDispute.buyer_unboxing_video}</span>
            <span className="mt-3 text-[10px] bg-red-950 text-red-400 px-2 py-0.5 rounded border border-red-500/30">
              Shows cracked blister upon box opening
            </span>
          </div>
        </div>
      </div>

      {/* Admin Arbitration Decision Console */}
      <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Arbitration Decision</h3>
        <div>
          <label className="block text-xs font-semibold text-gray-300 mb-1">Moderator Audit Ruling Notes *</label>
          <textarea
            rows={2}
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            placeholder="e.g. Courier impact during transit caused blister fracture. Buyer unboxing video confirms package seal was unopened prior..."
            className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-amber-500"
          />
        </div>
        <div className="flex flex-wrap gap-4 pt-2">
          <button
            onClick={() => handleResolve("REFUND_TO_BUYER")}
            className="bg-red-600 hover:bg-red-500 text-white font-bold py-2.5 px-5 rounded-xl text-xs transition shadow-lg shadow-red-900/30 flex items-center space-x-1.5"
          >
            <span>Ruling for Buyer: Refund Escrow (₹{activeDispute.escrow_amount_rupees})</span>
          </button>
          <button
            onClick={() => handleResolve("RELEASE_TO_SELLER")}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 px-5 rounded-xl text-xs transition shadow-lg shadow-emerald-900/30 flex items-center space-x-1.5"
          >
            <span>Ruling for Seller: Release Payout</span>
          </button>
        </div>
      </div>
    </div>
  );
}
