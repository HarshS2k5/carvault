# CarVault (🏎️ CV)

> **Trust-First Die-Cast Collectibles & Reselling Marketplace for India**

CarVault is an end-to-end, trust-first marketplace designed specifically for premium die-cast toy collectors (Hot Wheels, Matchbox, Kaido House, MiniGT, Tomica, Inno64).

Every listing is verified before it goes live. Every payment is held in escrow until delivery is verified. Counterfeits and fraud result in a permanent platform and bank ban.

---

## 🌟 Key Architecture & Pillars

1. **Mandatory Listing Review**:
   - Every listing requires physical proof with a unique handwritten verification code (`CV-XXXXX`) generated per listing session.
   - 4-point administrative checklist: Perceptual hash verification, reverse image deduplication, tamper inspection, and price-to-market boundary checks.
2. **Escrow & Split Payments**:
   - Platform acts as the escrow middle party via licensed gateway split accounts (Razorpay Route / Cashfree Easy Split).
   - Customer funds are never co-mingled in operational bank accounts.
3. **Double-Entry Financial Ledger**:
   - Immutable double-entry ledger tracking all transactions in integer paise (`₹1 = 100 paise`).
   - Balanced accounts: `buyer_funds_held`, `seller_payable`, `platform_commission`, `gateway_fees`, `escrow_refunds`.
   - Daily reconciliation jobs against gateway settlement logs.
4. **Order State Machine & Delivery OTP**:
   - Strict transition path: `CREATED` ➔ `PAID_HELD` ➔ `SHIPPED` ➔ `DELIVERED` ➔ `INSPECTION_WINDOW` ➔ `RELEASED`.
   - Seller packing video & buyer unboxing video audit trail for dispute arbitration.
5. **Universal Reporting & Anti-Fraud**:
   - Universal report modal on listings, seller profiles, orders, and chats.
   - Fraud penalty ladder: warning ➔ listing takedown ➔ escrow hold ➔ suspension ➔ permanent ban (device fingerprint & bank account blacklisted).
6. **AI Agent Ready**:
   - First-class agent endpoints with `schema.org` Product/Offer metadata.
   - Dedicated [llms.txt](http://localhost:3000/llms.txt) manifest and Model Context Protocol (MCP) tool integration.

---

## 📁 Repository Structure

```
carvault/
├── backend/                  # FastAPI Modular Monolith (Python 3.12)
│   ├── app/
│   │   ├── api/v1/          # Endpoints: auth, listings, orders, webhooks, ledger, disputes, public, mcp
│   │   ├── core/            # Config, database, state machine
│   │   ├── models/          # SQLAlchemy async models
│   │   ├── services/        # Review queue, ledger engine, courier, reconciliation
│   │   ├── main.py          # Application entrypoint
│   │   └── seed.py          # Database seeding
│   ├── tests/               # 20+ automated pytest test suites
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/                 # Next.js 14 App Router + Tailwind CSS
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Marketplace browse
│   │   │   ├── sell/page.tsx       # Sell wizard with physical verification code
│   │   │   ├── orders/[id]/        # Order stepper, delivery OTP & dispute flow
│   │   │   ├── admin/review/       # Admin review cockpit
│   │   │   ├── admin/disputes/     # Side-by-side video dispute arbitration
│   │   │   ├── admin/reports/      # Urgent anti-fraud report triage
│   │   │   ├── admin/finance/      # GMV, held escrow, balanced ledger accounts
│   │   │   ├── rules/page.tsx      # Rules & Grievance Officer details
│   │   │   ├── llms.txt/route.ts   # AI agent instruction manifest
│   │   │   └── sitemap.ts          # SEO sitemap
│   │   └── components/
│   │       └── report-modal.tsx    # Universal reporting modal
│   └── package.json
└── docs/
    └── COMPLIANCE_TODO.md    # Legal & Tax Compliance Roadmap (RBI, DPDP, GST, TDS/TCS)
```

---

## 🚀 Getting Started Locally

### Prerequisites
- Node.js 18+ (tested on Node.js 20 & 22)
- Python 3.11+ (tested on Python 3.12)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Marketplace: `http://localhost:3000`

### 3. Run Automated Tests
```bash
cd backend
pytest -v
```

---

## ⚖️ Compliance & Governance
CarVault adheres strictly to the Consumer Protection (E-Commerce) Rules 2020, Information Technology Intermediary Guidelines, and DPDP Act 2023. See [`docs/COMPLIANCE_TODO.md`](docs/COMPLIANCE_TODO.md) for full audit specifications.
