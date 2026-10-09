"use client";

import { useState } from "react";
import { ShieldAlert, AlertTriangle, CheckCircle2, UserX, Trash2, Ban, Eye } from "lucide-react";

export default function AdminReportsQueuePage() {
  const [reports, setReports] = useState([
    {
      id: "rep-1",
      reference_id: "REP-2026-X892K",
      priority: "URGENT",
      target_type: "LISTING",
      target_id: "list-fake-01",
      target_title: "1971 Datsun 510 STH Special",
      reason: "FAKE_ITEM",
      description: "Counterfeit rubber wheels glued on standard mainline baseplate. Tampo reproduction.",
      evidence_url: "https://media.carvault.in/fake_proof.jpg",
      contact_email: "collector_vigilante@gmail.com",
      status: "OPEN",
    },
    {
      id: "rep-2",
      reference_id: "REP-2026-B114M",
      priority: "URGENT",
      target_type: "PROFILE",
      target_id: "usr-offplatform-99",
      target_title: "Suspicious Seller Account",
      reason: "OFF_PLATFORM_PAYMENT",
      description: "Sent phone number and asked buyer to pay ₹1,000 via Google Pay to skip platform escrow.",
      evidence_url: null,
      contact_email: null,
      status: "OPEN",
    },
    {
      id: "rep-3",
      reference_id: "REP-2026-C440P",
      priority: "NORMAL",
      target_type: "LISTING",
      target_id: "list-blurry-02",
      target_title: "Porsche 911 GT3 RS",
      reason: "FAKE_PHOTOS_VIDEO",
      description: "Appears to be a stock catalog image from Google without verification code.",
      evidence_url: null,
      contact_email: null,
      status: "OPEN",
    },
  ]);

  const [actionNotice, setActionNotice] = useState("");

  const handleEnforce = (reportId: string, action: string) => {
    setReports(reports.map(r => r.id === reportId ? { ...r, status: "ACTION_TAKEN" } : r));
    if (action === "PERMANENT_BAN") {
      setActionNotice("🚨 ENFORCEMENT ACTION: User permanently banned. Associated device fingerprints and bank accounts blacklisted.");
    } else if (action === "REMOVE_LISTING") {
      setActionNotice("🗑 Listing immediately delisted and removed from marketplace search.");
    } else {
      setActionNotice(`Action ${action} executed.`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center space-x-1.5 text-xs font-bold uppercase tracking-wider text-red-400 bg-red-400/10 px-2.5 py-1 rounded border border-red-400/20 mb-2">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Universal Report Queue</span>
        </div>
        <h1 className="text-2xl font-black text-white">Trust & Safety Triage Queue</h1>
        <p className="text-gray-400 text-xs mt-1">
          Prioritized review of fraud, counterfeit items, resealed cards, and off-platform payment attempts.
        </p>
      </div>

      {actionNotice && (
        <div className="p-4 rounded-xl text-xs font-bold bg-amber-500/10 border border-amber-500/30 text-amber-300">
          {actionNotice}
        </div>
      )}

      {/* Reports Table */}
      <div className="space-y-4">
        {reports.map((rep) => (
          <div
            key={rep.id}
            className={`p-6 rounded-2xl border transition ${
              rep.status === "ACTION_TAKEN"
                ? "bg-gray-950/60 border-gray-800 opacity-60"
                : rep.priority === "URGENT"
                ? "bg-gradient-to-r from-red-950/30 via-gray-900 to-gray-900 border-red-500/40"
                : "bg-gray-900 border-gray-800"
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-800/80 pb-4 mb-4">
              <div className="flex items-center space-x-3">
                <span className={`px-2.5 py-0.5 rounded text-[11px] font-bold ${
                  rep.priority === "URGENT" ? "bg-red-600 text-white" : "bg-gray-800 text-gray-300"
                }`}>
                  {rep.priority}
                </span>
                <span className="font-mono text-xs font-bold text-amber-400">{rep.reference_id}</span>
                <span className="text-xs text-gray-400 font-semibold">&bull; Target: {rep.target_type} ({rep.target_title})</span>
              </div>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                rep.status === "ACTION_TAKEN"
                  ? "bg-emerald-950 text-emerald-400 border-emerald-500/30"
                  : "bg-amber-950 text-amber-400 border-amber-500/30"
              }`}>
                {rep.status}
              </span>
            </div>

            <div className="space-y-2 mb-5">
              <div className="text-xs font-bold text-red-300 uppercase tracking-wide">
                Reason: {rep.reason.replace("_", " ")}
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">
                "{rep.description}"
              </p>
              {rep.evidence_url && (
                <div className="text-[11px] text-gray-400 pt-1">
                  Attached Proof: <a href={rep.evidence_url} target="_blank" rel="noreferrer" className="text-amber-400 underline font-mono">{rep.evidence_url}</a>
                </div>
              )}
            </div>

            {/* Action Bar */}
            {rep.status === "OPEN" && (
              <div className="flex flex-wrap gap-3 pt-3 border-t border-gray-800">
                <button
                  onClick={() => handleEnforce(rep.id, "PERMANENT_BAN")}
                  className="bg-red-700 hover:bg-red-600 text-white font-bold py-2 px-4 rounded-lg text-xs transition flex items-center space-x-1.5 shadow-lg shadow-red-950/40"
                >
                  <Ban className="w-3.5 h-3.5" />
                  <span>Permanent Ban & Device Blacklist</span>
                </button>
                <button
                  onClick={() => handleEnforce(rep.id, "REMOVE_LISTING")}
                  className="bg-gray-800 hover:bg-gray-700 text-gray-200 font-semibold py-2 px-3 rounded-lg text-xs transition border border-gray-700 flex items-center space-x-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delist Item</span>
                </button>
                <button
                  onClick={() => handleEnforce(rep.id, "DISMISS")}
                  className="text-gray-500 hover:text-gray-300 text-xs py-2 px-3 font-medium transition"
                >
                  Dismiss Report
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
