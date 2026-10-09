"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { ShieldCheck, Package, Clock, CheckCircle2, AlertOctagon, ArrowRight, Truck } from "lucide-react";

export default function OrderTrackingPage() {
  const params = useParams();
  const orderId = params?.id || "demo-ord-1";

  const [order, setOrder] = useState({
    id: orderId,
    current_state: "INSPECTION_WINDOW", // Demo state
    item_title: "Nissan Skyline GT-R R34 Car Culture - Mint Blister",
    total_paid_rupees: 1550,
    commission_rupees: 46.5,
    seller_payable_rupees: 1503.5,
    tracking_id: "DELHI-981240-IN",
    courier_partner: "DELHIVERY",
    inspection_hours_left: 36,
  });

  const [deliveryOtp, setDeliveryOtp] = useState("");
  const [disputeReason, setDisputeReason] = useState("");
  const [showDisputeModal, setShowDisputeModal] = useState(false);
  const [statusNotice, setStatusNotice] = useState("");

  const steps = [
    { key: "CREATED", label: "Created" },
    { key: "PAID_HELD", label: "Paid (Escrow Held)" },
    { key: "SHIPPED", label: "Shipped" },
    { key: "DELIVERED", label: "Delivered" },
    { key: "INSPECTION_WINDOW", label: "48h Inspection" },
    { key: "RELEASED", label: "Payout Released" },
  ];

  const currentStepIndex = steps.findIndex((s) => s.key === order.current_state);

  const handleAcceptInspection = () => {
    setOrder({ ...order, current_state: "RELEASED" });
    setStatusNotice("✅ Inspection accepted! Funds released to seller's verified bank account.");
  };

  const handleRaiseDispute = () => {
    if (!disputeReason) return;
    setOrder({ ...order, current_state: "DISPUTED" });
    setShowDisputeModal(false);
    setStatusNotice("⚠ Escrow frozen! Dispute case opened. Admin moderator is reviewing unboxing evidence.");
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center space-x-1.5 text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-400/10 px-2.5 py-1 rounded border border-amber-400/20 mb-2">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Escrow Protected Order</span>
        </div>
        <h1 className="text-2xl font-black text-white">Order #{order.id}</h1>
        <p className="text-gray-400 text-xs mt-1">
          Funds are held in licensed gateway escrow until delivery verification and inspection window completion.
        </p>
      </div>

      {statusNotice && (
        <div className="bg-amber-500/10 border border-amber-500/30 text-amber-300 p-4 rounded-xl text-xs font-semibold">
          {statusNotice}
        </div>
      )}

      {/* Escrow State Machine Progress Stepper */}
      <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-6">
          Escrow State Machine Status
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {steps.map((step, idx) => {
            const isCompleted = idx <= (currentStepIndex === -1 ? 4 : currentStepIndex);
            const isCurrent = step.key === order.current_state;
            return (
              <div
                key={step.key}
                className={`p-3 rounded-xl border text-center transition ${
                  isCurrent
                    ? "bg-amber-500/10 border-amber-500 text-amber-300 ring-1 ring-amber-500/30"
                    : isCompleted
                    ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-400"
                    : "bg-gray-950 border-gray-800 text-gray-600"
                }`}
              >
                <div className="text-[10px] font-mono font-bold uppercase mb-1">Step {idx + 1}</div>
                <div className="text-xs font-bold">{step.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Order Item & Escrow Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-gray-900 border border-gray-800 p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Item Details</h3>
          <div className="flex gap-4">
            <div className="w-20 h-20 bg-gray-950 rounded-lg overflow-hidden flex-shrink-0 border border-gray-800">
              <img
                src="https://images.unsplash.com/photo-1581235720704-06d3acfcb36f?w=400"
                alt="Diecast Car"
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <h4 className="font-bold text-white text-sm">{order.item_title}</h4>
              <p className="text-xs text-gray-400 mt-1">Tracking ID: <span className="font-mono text-gray-200">{order.tracking_id}</span> ({order.courier_partner})</p>
              <span className="inline-block mt-2 bg-emerald-950 text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-500/30">
                PHYSICAL CODE VERIFIED
              </span>
            </div>
          </div>

          {/* Inspection Window Action Box */}
          {order.current_state === "INSPECTION_WINDOW" && (
            <div className="bg-amber-950/40 border border-amber-500/40 p-4 rounded-xl space-y-3 mt-4">
              <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold">
                <Clock className="w-4 h-4" />
                <span>Inspection Window Active ({order.inspection_hours_left} Hours Remaining)</span>
              </div>
              <p className="text-gray-300 text-xs leading-relaxed">
                Check the blister packaging, corners, baseplate casting code, and wheels. If satisfied, release the payout to the seller. If damaged or counterfeit, freeze escrow by raising a dispute.
              </p>
              <div className="flex gap-3 pt-1">
                <button
                  onClick={handleAcceptInspection}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-4 py-2 rounded-lg text-xs transition shadow-lg shadow-emerald-900/40"
                >
                  ✓ Accept Item & Release Payout
                </button>
                <button
                  onClick={() => setShowDisputeModal(true)}
                  className="bg-red-800/80 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded-lg text-xs transition border border-red-700"
                >
                  ⚠ Raise Inspection Dispute
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Financial Escrow Summary */}
        <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Escrow Ledger</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-gray-300">
              <span>Buyer Paid:</span>
              <span className="font-bold text-white">₹{order.total_paid_rupees}</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Platform Fee (3%):</span>
              <span>-₹{order.commission_rupees}</span>
            </div>
            <div className="pt-2 border-t border-gray-800 flex justify-between font-bold text-amber-400 text-sm">
              <span>Seller Payable:</span>
              <span>₹{order.seller_payable_rupees}</span>
            </div>
          </div>
          <div className="text-[11px] text-gray-500 pt-3 border-t border-gray-800">
            Funds currently held in Razorpay Route escrow subaccount. Payout settles directly to seller bank upon release.
          </div>
        </div>
      </div>

      {/* Dispute Modal */}
      {showDisputeModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center space-x-2 text-red-400 text-sm font-bold">
              <AlertOctagon className="w-5 h-5" />
              <span>Raise Inspection Claim (Freeze Escrow)</span>
            </div>
            <p className="text-gray-300 text-xs leading-relaxed">
              Describe why the delivered die-cast does not match the approved listing. Payout to the seller will be immediately frozen.
            </p>
            <textarea
              rows={3}
              required
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              placeholder="e.g. Card has cracked blister bubble not shown in verification photos..."
              className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-red-500"
            />
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowDisputeModal(false)}
                className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleRaiseDispute}
                className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-lg text-xs font-bold"
              >
                Freeze Escrow & Open Dispute
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
