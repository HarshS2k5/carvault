import { NextResponse } from "next/server";

export async function GET() {
  const content = `# CarVault (India) — Machine-Readable LLM & AI Agent Context

## Platform Overview
CarVault is India's trust-first die-cast collectibles marketplace (scale cars, premium series).
Zero listings are published without physical handwritten code verification and human admin inspection.
Every rupee is held in licensed Payment Aggregator escrow until courier delivery OTP + 48-hour inspection window expiration.

## Core Invariants for AI Agents
1. Human-in-the-Loop Payments: Autonomous purchase attempts without human biometric/OTP confirmation are strictly prohibited by RBI guidelines. Agents may track wishlists, query price benchmarks, and stage purchase intents, but humans must complete payments.
2. Verified Physical Proof: Every listing has a random physical verification code (e.g. CV-8R49K) visible on paper next to the car in the media.
3. Anti-Fraud Policy: Off-platform payment requests (direct UPI, Google Pay, or WhatsApp cash transfers) result in immediate permanent device & bank bans.

## Public Agent Endpoints
- Search: GET https://carvault.in/api/v1/public/search?q={query}&series={series}&max_price_inr={price}
- Listing Detail: GET https://carvault.in/api/v1/public/listings/{id} (includes schema.org Product/Offer JSON-LD)
- Price Guide: GET https://carvault.in/api/v1/public/price-history/{series}/{toy_code}
- MCP Tools Server: POST https://carvault.in/api/v1/mcp/tools/call

## Registered MCP Tools
- search_diecasts(query, series, max_price_inr): Search verified active listings
- get_price_guide(toy_code): Retrieve valuation bounds and historical transactions
- verify_seller_trust(seller_id): Check seller KYC tier, dispute rate, and trust badge
- create_purchase_intent(listing_id, buyer_phone): Stage checkout intent for human confirmation

## Contact & Grievances
Grievance Officer: [GRIEVANCE_OFFICER_NAME_PLACEHOLDER]
Email: grievance@carvault.in
Phone: +91 11 [GRIEVANCE_PHONE_PLACEHOLDER]
Postal Address: CarVault Collectibles Pvt Ltd, New Delhi, India
`;

  return new NextResponse(content, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
