# CarVault Compliance & Legal Checklist (TODO for Legal Counsel / CA)

> [!IMPORTANT]
> The following items must be vetted by a qualified Indian Chartered Accountant (CA) and legal counsel specializing in fintech and e-commerce intermediary regulations before processing production payments or live listings.

---

### 1. Reserve Bank of India (RBI) Payment Aggregator & Escrow Regulations
- **Split Payment Architecture**: The platform integrates licensed Payment Aggregator marketplace split engines (**Razorpay Route** or **Cashfree Easy Split**).
  - *Rule*: Platform bank accounts must NEVER receive, hold, or pool buyer funds. Funds move directly from the buyer's account to the Payment Aggregator nodal/escrow account, and are settled directly to the seller's KYC-verified bank account upon delivery verification.
  - *Action*: Ensure merchant agreement with the payment gateway formally designates the platform as a marketplace facilitator under RBI Guidelines for Payment Aggregators (circular DPSS.CO.PD.No.1810/02.14.008/2019-20).

---

### 2. Digital Personal Data Protection (DPDP) Act 2023 & Aadhaar Regulations
- **Zero Aadhaar Storage Policy**:
  - *Rule*: CarVault NEVER stores 12-digit Aadhaar numbers, biometric data, or unmasked PAN details in any database table.
  - *Implementation*: Authentication uses DigiLocker sandbox / authorized e-KYC providers returning hashed user reference IDs and UIDAI-approved masked representations (e.g. `ABCDE****F`).
- **Data Minimization & Encryption**:
  - KYC documents, bank IFSC details, and selfie liveness proofs are AES-256 encrypted at rest in S3/R2 storage with restricted IAM keys.
  - Consent capture for phone number, device fingerprints, and delivery coordinates.

---

### 3. Goods and Services Tax (GST) & Income Tax TDS/TCS
- **Marketplace Commission GST**:
  - CarVault charges a commission (0-3% in beta, 6-8% at launch) + minimum fee per order.
  - GST of 18% must be levied on the platform commission (HSN/SAC 998599 or 998313). Tax invoices must be issued to sellers for the platform commission.
- **TCS under GST (Section 52 of CGST Act)**:
  - E-commerce operators are required to collect TCS at 1% (0.5% CGST + 0.5% SGST or 1% IGST) on the net value of taxable supplies made through the platform by other suppliers.
- **TDS under Income Tax (Section 194-O)**:
  - TDS of 0.1% / 1% on the gross amount of sales facilitated through the marketplace for individual/HUF sellers crossing statutory annual thresholds.
  - *Action*: Confirm with CA regarding threshold exemption monitoring in automated settlement reports.

---

### 4. Consumer Protection (E-Commerce) Rules 2020 & IT Intermediary Rules 2021
- **Grievance Redressal Mechanism**:
  - Appoint a designated **Grievance Officer** resident in India.
  - Contact details (Name, Email, Physical Address, Phone number) displayed prominently on the `/rules` and platform footer.
  - Mandatory 48-hour acknowledgment and 30-day resolution timeline for customer disputes.
- **Intermediary Due Diligence (Rule 3)**:
  - Clear terms of service regarding prohibited items (counterfeit cars, copyright infringements, non-diecast contraband).
  - Anti-fraud penalty ladder documented: Warning -> Listing Removal -> Escrow Freeze -> Permanent Account Ban -> Referral to Law Enforcement.
