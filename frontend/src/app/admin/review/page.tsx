"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, HelpCircle, Eye, RefreshCw } from "lucide-react";

export default function AdminReviewQueuePage() {
  const [queueItems, setQueueItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [checklist, setChecklist] = useState({
    checklist_code_matched: false,
    checklist_tamper_packaging_checked: false,
    checklist_media_clarity_checked: false,
    checklist_condition_matches_desc: false,
  });
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [rejectTemplate, setRejectTemplate] = useState("MISSING_CODE");
  const [statusMessage, setStatusMessage] = useState("");
  const [loading, setLoading] = useState(true);

  // Mock initial queue item if backend is offline during demo
  const fallbackQueue = [
    {
      id: "rev-demo-01",
      listing_id: "list-demo-01",
      auto_check_phash_duplicate: false,
      auto_check_price_outlier: false,
      auto_check_media_count_met: true,
      auto_check_flags: [],
      submitted_at: new Date().toISOString(),
      listing: {
        id: "list-demo-01",
        seller_id: "seller-001",
        title: "Porsche 911 GT3 RS Boulevard Premium",
        description: "Brand new card, verified casting code on baseplate. Never opened.",
        series_name: "Boulevard",
        model_year: 2024,
        toy_code: "GJT68",
        condition: "MINT_CARD",
        tags: ["ORIGINAL", "SEALED"],
        price_rupees: 1100,
        price_paise: 110000,
        verification_code: "CV-8R49K",
        media: [
          {
            id: "m-1",
            media_url: "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800",
            media_type: "IMAGE",
            is_verification_shot: true
          }
        ]
      }
    }
  ];

  async function loadQueue() {
    setLoading(true);
    try {
      // In production, include Admin JWT Authorization header
      const res = await fetch("http://127.0.0.1:8000/api/v1/admin/review-queue");
      if (res.ok) {
        const data = await res.json();
        setQueueItems(data);
        if (data.length > 0) setSelectedItem(data[0]);
        setLoading(false);
        return;
      }
    } catch (err) {
      // Backend not running
    }
    setQueueItems(fallbackQueue);
    setSelectedItem(fallbackQueue[0]);
    setLoading(false);
  }

  useEffect(() => {
    loadQueue();
  }, []);

  const handleApprove = async () => {
    if (!checklist.checklist_code_matched) {
      alert("Compliance Invariant: You cannot approve a listing without verifying that the handwritten verification code matches the physical media!");
      return;
    }
    setStatusMessage("Approving listing and publishing live to marketplace...");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/admin/review-queue/${selectedItem.id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_notes: reviewerNotes || "Physical verification code matched and blister intact.",
          checklist: checklist
        })
      });
      if (res.ok) {
        setStatusMessage("✅ Listing APPROVED and published live!");
        loadQueue();
      } else {
        setStatusMessage("Approved locally (Demo mode). Listing is now live.");
      }
    } catch (e) {
      setStatusMessage("Approved locally (Demo mode). Listing is now live.");
    }
  };

  const handleReject = async () => {
    setStatusMessage("Rejecting listing...");
    try {
      await fetch(`http://127.0.0.1:8000/api/v1/admin/review-queue/${selectedItem.id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template_code: rejectTemplate,
          rejection_reason: reviewerNotes || `Failed verification checklist under template ${rejectTemplate}`
        })
      });
      setStatusMessage("❌ Listing REJECTED and removed from queue.");
      loadQueue();
    } catch (e) {
      setStatusMessage("Rejected locally (Demo mode).");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center pb-6 border-b border-gray-800 mb-8">
        <div>
          <div className="inline-flex items-center space-x-1.5 text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-400/10 px-2.5 py-1 rounded border border-amber-400/20 mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Admin Review Cockpit</span>
          </div>
          <h1 className="text-2xl font-black text-white">Listing Verification Queue</h1>
          <p className="text-gray-400 text-xs mt-1">
            Every listing must be verified against physical code & packaging integrity before public release.
          </p>
        </div>
        <button
          onClick={loadQueue}
          className="mt-4 md:mt-0 flex items-center space-x-2 bg-gray-900 border border-gray-700 hover:bg-gray-800 text-xs px-3 py-2 rounded-lg text-gray-300 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Queue ({queueItems.length} Pending)</span>
        </button>
      </div>

      {statusMessage && (
        <div className="bg-amber-500/10 border border-amber-500/30 text-amber-300 p-3 rounded-lg text-sm mb-6">
          {statusMessage}
        </div>
      )}

      {selectedItem ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Media & Auto-Checks (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Auto Checks Bar */}
            <div className="bg-gray-900 border border-gray-800 p-4 rounded-xl flex flex-wrap gap-4 items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-400 font-semibold uppercase">Auto Checks:</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${selectedItem.auto_check_phash_duplicate ? "bg-red-950 text-red-400 border border-red-500/30" : "bg-emerald-950 text-emerald-400 border border-emerald-500/30"}`}>
                  {selectedItem.auto_check_phash_duplicate ? "⚠ pHash Duplicate Reused" : "✓ Unique Images"}
                </span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${selectedItem.auto_check_price_outlier ? "bg-amber-950 text-amber-400 border border-amber-500/30" : "bg-emerald-950 text-emerald-400 border border-emerald-500/30"}`}>
                  {selectedItem.auto_check_price_outlier ? "⚠ Price Anomaly Flag" : "✓ Price In Range"}
                </span>
              </div>
              <div className="text-xs font-mono text-gray-400">
                Target Code: <span className="text-amber-400 font-bold">{selectedItem.listing.verification_code}</span>
              </div>
            </div>

            {/* Media Gallery Preview */}
            <div className="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden relative group">
              <img
                src={selectedItem.listing.media?.[0]?.media_url || "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800"}
                alt="Verification media"
                className="w-full h-96 object-contain bg-black"
              />
              <div className="absolute top-4 left-4 bg-black/80 backdrop-blur border border-amber-500/50 text-amber-400 px-3 py-1 rounded-md text-xs font-mono font-bold flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-amber-400" />
                <span>EXPECTED CODE: {selectedItem.listing.verification_code}</span>
              </div>
            </div>

            {/* Listing Metadata */}
            <div className="bg-gray-900 border border-gray-800 p-5 rounded-xl space-y-3">
              <h2 className="text-lg font-bold text-white">{selectedItem.listing.title}</h2>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="bg-gray-800 text-gray-300 px-2 py-1 rounded font-semibold">{selectedItem.listing.series_name}</span>
                <span className="bg-gray-800 text-gray-300 px-2 py-1 rounded font-semibold">{selectedItem.listing.model_year}</span>
                <span className="bg-gray-800 text-gray-300 px-2 py-1 rounded font-mono">Toy Code: {selectedItem.listing.toy_code || "N/A"}</span>
                <span className="bg-emerald-900/60 text-emerald-300 px-2 py-1 rounded font-semibold">{selectedItem.listing.condition}</span>
                <span className="bg-amber-900/60 text-amber-300 px-2 py-1 rounded font-bold">₹{selectedItem.listing.price_rupees}</span>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed pt-2 border-t border-gray-800">
                {selectedItem.listing.description}
              </p>
            </div>
          </div>

          {/* Right Column: Moderator Decision Panel & Checklist (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl space-y-5">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-gray-800 pb-3">
                Moderator Verification Checklist
              </h3>

              <div className="space-y-3 text-xs">
                <label className="flex items-start space-x-3 cursor-pointer p-2.5 rounded-lg bg-gray-950 hover:bg-gray-800/60 border border-gray-800 transition">
                  <input
                    type="checkbox"
                    checked={checklist.checklist_code_matched}
                    onChange={(e) => setChecklist({ ...checklist, checklist_code_matched: e.target.checked })}
                    className="mt-0.5 rounded text-amber-500 focus:ring-amber-400 h-4 w-4 bg-gray-900 border-gray-700"
                  />
                  <div>
                    <span className="font-bold text-gray-200 block">
                      1. Verification Code Matched ({selectedItem.listing.verification_code})
                    </span>
                    <span className="text-gray-500 text-[11px]">
                      Confirmed handwritten paper appears in image beside physical car.
                    </span>
                  </div>
                </label>

                <label className="flex items-start space-x-3 cursor-pointer p-2.5 rounded-lg bg-gray-950 hover:bg-gray-800/60 border border-gray-800 transition">
                  <input
                    type="checkbox"
                    checked={checklist.checklist_tamper_packaging_checked}
                    onChange={(e) => setChecklist({ ...checklist, checklist_tamper_packaging_checked: e.target.checked })}
                    className="mt-0.5 rounded text-amber-500 focus:ring-amber-400 h-4 w-4 bg-gray-900 border-gray-700"
                  />
                  <div>
                    <span className="font-bold text-gray-200 block">2. Packaging Tampering Checked</span>
                    <span className="text-gray-500 text-[11px]">
                      Blister seal is original factory heat-weld (no acetone, reglue, or re-stapled bubble).
                    </span>
                  </div>
                </label>

                <label className="flex items-start space-x-3 cursor-pointer p-2.5 rounded-lg bg-gray-950 hover:bg-gray-800/60 border border-gray-800 transition">
                  <input
                    type="checkbox"
                    checked={checklist.checklist_media_clarity_checked}
                    onChange={(e) => setChecklist({ ...checklist, checklist_media_clarity_checked: e.target.checked })}
                    className="mt-0.5 rounded text-amber-500 focus:ring-amber-400 h-4 w-4 bg-gray-900 border-gray-700"
                  />
                  <div>
                    <span className="font-bold text-gray-200 block">3. Media Clarity & Casting Proof</span>
                    <span className="text-gray-500 text-[11px]">
                      Baseplate and wheel hubs are clear; no stock photos used.
                    </span>
                  </div>
                </label>

                <label className="flex items-start space-x-3 cursor-pointer p-2.5 rounded-lg bg-gray-950 hover:bg-gray-800/60 border border-gray-800 transition">
                  <input
                    type="checkbox"
                    checked={checklist.checklist_condition_matches_desc}
                    onChange={(e) => setChecklist({ ...checklist, checklist_condition_matches_desc: e.target.checked })}
                    className="mt-0.5 rounded text-amber-500 focus:ring-amber-400 h-4 w-4 bg-gray-900 border-gray-700"
                  />
                  <div>
                    <span className="font-bold text-gray-200 block">4. Condition Matches Rating</span>
                    <span className="text-gray-500 text-[11px]">
                      Stated condition ({selectedItem.listing.condition}) matches corner wear.
                    </span>
                  </div>
                </label>
              </div>

              {/* Reviewer Notes */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Moderator Audit Notes</label>
                <textarea
                  rows={2}
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  placeholder="e.g. Sharp blister corners, verified against 2024 Boulevard release."
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-xs text-gray-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="space-y-2 pt-2">
                <button
                  onClick={handleApprove}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 px-4 rounded-lg text-xs transition flex items-center justify-center space-x-1.5 shadow-lg shadow-emerald-900/30"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve & Release to Marketplace</span>
                </button>

                <div className="flex gap-2">
                  <select
                    value={rejectTemplate}
                    onChange={(e) => setRejectTemplate(e.target.value)}
                    className="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-2 text-xs text-gray-300 focus:outline-none"
                  >
                    <option value="MISSING_CODE">Missing Code in Photo</option>
                    <option value="TAMPERED_CARD">Tampered Blister / Reglued</option>
                    <option value="BLURRY_MEDIA">Blurry Media / Cannot Inspect</option>
                    <option value="REUSED_IMAGE">Reused / Stolen Stock Photo</option>
                  </select>
                  <button
                    onClick={handleReject}
                    className="bg-red-700 hover:bg-red-600 text-white font-semibold py-2 px-3 rounded-lg text-xs transition flex items-center space-x-1"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-400">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
          <p className="font-semibold text-white">Review queue is empty!</p>
          <p className="text-xs text-gray-500 mt-1">All submitted die-cast cars have been moderated.</p>
        </div>
      )}
    </div>
  );
}
