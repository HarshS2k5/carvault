import { ShieldAlert, AlertTriangle, Scale, Mail, Phone, UserCheck, CheckCircle2 } from "lucide-react";

export default function RulesPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12 space-y-12">
      {/* Title */}
      <div>
        <div className="inline-flex items-center space-x-2 bg-amber-500/10 border border-amber-500/30 px-3 py-1 rounded-full text-amber-400 text-xs font-semibold mb-3">
          <Scale className="w-4 h-4 text-amber-400" />
          <span>Statutory Terms & Trust Guidelines</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">CarVault Rules & Anti-Fraud Policy</h1>
        <p className="text-gray-400 text-sm mt-2 leading-relaxed">
          CarVault is a trust-first marketplace. Our platform enforces pre-publication physical inspections and payment escrow to protect die-cast collectors. Fraud and counterfeit attempts carry permanent bans.
        </p>
      </div>

      {/* 1. Prohibited Items */}
      <section id="prohibited" className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center space-x-2 text-red-400">
          <ShieldAlert className="w-5 h-5" />
          <h2 className="text-lg font-bold text-white">1. Strictly Prohibited Items</h2>
        </div>
        <ul className="list-disc list-inside text-xs text-gray-300 space-y-2 leading-relaxed">
          <li><strong>Counterfeit / Bootleg Castings:</strong> Unlicensed replicas, fraudulent tampo/decal reproductions, or fake factory wheel swaps passed as genuine.</li>
          <li><strong>Resealed / Glued Blister Cards:</strong> Items resealed with acetone, glue, or double-sided tape represented as unopened or factory-mint.</li>
          <li><strong>Stolen Stock Photography:</strong> Photos downloaded from online auctions, social media groups, or manufacturers without physical ownership.</li>
          <li><strong>Non-Diecast Collectibles:</strong> Any goods outside scale model vehicles, accessories, and display cases.</li>
        </ul>
      </section>

      {/* 2. Listing Rules */}
      <section className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">2. Listing & Verification Requirements</h2>
        <div className="space-y-3 text-xs text-gray-300 leading-relaxed">
          <p>
            <strong>Physical Code Requirement:</strong> Every listing must include a clearly focused photo of the die-cast car next to a handwritten slip bearing the unique listing verification code.
          </p>
          <p>
            <strong>Accurate Condition Grading:</strong> Card creases, soft corners, blister cracks, paint chips, and axle bends must be highlighted in photos and stated in the description.
          </p>
          <p>
            <strong>Mandatory Admin Moderation:</strong> Zero listings go live immediately. All submissions enter the Admin Review Queue and must be validated by a certified moderator.
          </p>
        </div>
      </section>

      {/* 3. Escrow & Payment Rules */}
      <section className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">3. Payment & Escrow Rules</h2>
        <div className="space-y-3 text-xs text-gray-300 leading-relaxed">
          <p>
            <strong>No Direct P2P Transfers:</strong> All transactions are settled via licensed payment gateway split accounts. Requesting direct UPI transfers, Google Pay, or bank deposits off-platform is strictly prohibited and results in an instant ban.
          </p>
          <p>
            <strong>Payout Gating:</strong> Seller payouts are held in licensed gateway escrow until delivery OTP verification + the 48-hour buyer inspection window has passed.
          </p>
        </div>
      </section>

      {/* 4. Penalty Ladder */}
      <section id="ladder" className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center space-x-2 text-amber-400">
          <AlertTriangle className="w-5 h-5" />
          <h2 className="text-lg font-bold text-white">4. Anti-Fraud Penalty Ladder</h2>
        </div>
        <div className="space-y-3">
          <div className="bg-gray-950 p-3.5 rounded-lg border border-gray-800">
            <span className="text-amber-400 font-bold text-xs">Stage 1: Warning & Listing Delisting</span>
            <p className="text-gray-400 text-xs mt-1">Applied for minor miscategorizations or unclear photos.</p>
          </div>
          <div className="bg-gray-950 p-3.5 rounded-lg border border-gray-800">
            <span className="text-orange-400 font-bold text-xs">Stage 2: Payout Hold & Review Downgrade</span>
            <p className="text-gray-400 text-xs mt-1">Applied for disputed items, delayed dispatch, or repeat misrepresentation.</p>
          </div>
          <div className="bg-gray-950 p-3.5 rounded-lg border border-gray-800">
            <span className="text-red-400 font-bold text-xs">Stage 3: Account Suspension</span>
            <p className="text-gray-400 text-xs mt-1">Active listings frozen for 14-30 days pending formal dispute investigation.</p>
          </div>
          <div className="bg-gray-950 p-3.5 rounded-lg border border-red-900/50">
            <span className="text-red-500 font-bold text-xs">Stage 4: Permanent Ban + Device & Bank Blacklist</span>
            <p className="text-gray-400 text-xs mt-1">
              Imposed for counterfeit die-cast dispatch, resealed cards, or off-platform payment solicitation. The user's device fingerprint, bank account, and phone number are permanently blocked.
            </p>
          </div>
          <div className="bg-gray-950 p-3.5 rounded-lg border border-purple-900/50">
            <span className="text-purple-400 font-bold text-xs">Stage 5: Law Enforcement Referral</span>
            <p className="text-gray-400 text-xs mt-1">
              Substantial fraud cases involving fraudulent mail shipments are formally reported to Indian Cyber Crime authorities (cybercrime.gov.in) with audit logs and KYC proofs.
            </p>
          </div>
        </div>
      </section>

      {/* 5. Statutory Grievance Redressal Mechanism */}
      <section className="bg-gradient-to-r from-gray-900 to-amber-950/40 border border-amber-500/30 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">5. Statutory Grievance Redressal (India)</h2>
        <p className="text-xs text-gray-300 leading-relaxed">
          In compliance with the Consumer Protection (E-Commerce) Rules, 2020 and Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021, the contact details of the platform Grievance Officer are set out below:
        </p>

        <div className="bg-gray-950/80 border border-gray-800 p-4 rounded-lg space-y-2 text-xs text-gray-300 font-mono">
          <div><strong className="text-gray-400">Designated Officer:</strong> [GRIEVANCE_OFFICER_NAME_PLACEHOLDER]</div>
          <div><strong className="text-gray-400">Email:</strong> grievance@carvault.in</div>
          <div><strong className="text-gray-400">Phone:</strong> +91 11 [GRIEVANCE_PHONE_PLACEHOLDER]</div>
          <div><strong className="text-gray-400">Postal Address:</strong> CarVault Collectibles Pvt Ltd, [REGISTERED_OFFICE_ADDRESS_PLACEHOLDER], New Delhi, India</div>
          <div><strong className="text-gray-400">Response SLA:</strong> Acknowledgment within 48 hours; resolution within 30 days.</div>
        </div>
      </section>
    </div>
  );
}
