# Tests for double-entry ledger zero-sum invariants, journal balancing, and daily settlement reconciliation
from datetime import date
import pytest
from app.models.ledger import EntryDirection
from app.models.order import Order, OrderState
from app.services.ledger_service import (
    record_balanced_transaction,
    record_payment_captured_ledger,
    record_escrow_payout_release_ledger,
    record_order_refund_ledger,
    get_account_balances,
    LedgerImbalanceError
)
from app.services.reconciliation_service import run_daily_settlement_reconciliation

@pytest.mark.asyncio
async def test_ledger_zero_sum_invariant_and_imbalance_prevention(test_db):
    # 1. Attempting an imbalanced transaction MUST raise LedgerImbalanceError
    imbalanced_entries = [
        {"account_code": "ASSET_ESCROW_NODAL", "direction": EntryDirection.DEBIT, "amount_paise": 100000}, # ₹1,000
        {"account_code": "LIABILITY_BUYER_FUNDS_HELD", "direction": EntryDirection.CREDIT, "amount_paise": 95000} # ₹950 (imbalance!)
    ]
    with pytest.raises(LedgerImbalanceError) as exc_info:
        await record_balanced_transaction(
            order_id="test_ord_1",
            transaction_type="TEST_TX",
            reference_id="ref_1",
            description="Testing imbalance detection",
            entries=imbalanced_entries,
            db=test_db
        )
    assert "Double-entry ledger imbalance detected" in str(exc_info.value)

    # 2. Balanced transaction succeeds
    balanced_entries = [
        {"account_code": "ASSET_ESCROW_NODAL", "direction": EntryDirection.DEBIT, "amount_paise": 100000},
        {"account_code": "LIABILITY_BUYER_FUNDS_HELD", "direction": EntryDirection.CREDIT, "amount_paise": 100000}
    ]
    tx = await record_balanced_transaction(
        order_id="test_ord_1",
        transaction_type="TEST_TX",
        reference_id="ref_2",
        description="Testing balanced entry",
        entries=balanced_entries,
        db=test_db
    )
    assert tx.id is not None
    assert len(tx.entries) == 2

@pytest.mark.asyncio
async def test_order_payment_capture_and_payout_release_ledger(test_db, buyer_user, seller_user, approved_listing):
    # Setup test order (₹1,500 total, 3% commission = ₹45, seller payable = ₹1,455)
    order = Order(
        listing_id=approved_listing.id,
        buyer_id=buyer_user.id,
        seller_id=seller_user.id,
        current_state=OrderState.CREATED,
        item_price_paise=150000,
        shipping_fee_paise=0,
        commission_rate_bps=300,
        commission_paise=4500,
        seller_payable_paise=145500,
        total_buyer_paid_paise=150000,
        gateway_order_id="order_rzp_ledger_test"
    )
    test_db.add(order)
    await test_db.commit()
    await test_db.refresh(order)

    # 1. Record payment capture journal entry
    cap_tx = await record_payment_captured_ledger(order, "pay_capture_999", test_db)
    assert cap_tx.transaction_type == "ORDER_PAYMENT_CAPTURED"

    # Verify balances after capture:
    # ASSET_ESCROW_NODAL: ₹1,500
    # LIABILITY_BUYER_FUNDS_HELD: ₹1,500
    # LIABILITY_SELLER_PAYABLE: ₹0
    # REVENUE_PLATFORM_COMMISSION: ₹0
    balances_step1 = {b["account_code"]: b["net_balance_paise"] for b in await get_account_balances(test_db)}
    assert balances_step1["ASSET_ESCROW_NODAL"] == 150000
    assert balances_step1["LIABILITY_BUYER_FUNDS_HELD"] == 150000
    assert balances_step1["LIABILITY_SELLER_PAYABLE"] == 0
    assert balances_step1["REVENUE_PLATFORM_COMMISSION"] == 0

    # 2. Record payout release after delivery inspection
    rel_tx = await record_escrow_payout_release_ledger(order, test_db)
    assert rel_tx.transaction_type == "ESCROW_PAYOUT_RELEASE"

    # Verify balances after release:
    # ASSET_ESCROW_NODAL: ₹1,500
    # LIABILITY_BUYER_FUNDS_HELD: ₹0 (obligation discharged)
    # LIABILITY_SELLER_PAYABLE: ₹1,455 (owed to seller bank account)
    # REVENUE_PLATFORM_COMMISSION: ₹45 (earned platform revenue)
    balances_step2 = {b["account_code"]: b["net_balance_paise"] for b in await get_account_balances(test_db)}
    assert balances_step2["ASSET_ESCROW_NODAL"] == 150000
    assert balances_step2["LIABILITY_BUYER_FUNDS_HELD"] == 0
    assert balances_step2["LIABILITY_SELLER_PAYABLE"] == 145500
    assert balances_step2["REVENUE_PLATFORM_COMMISSION"] == 4500

@pytest.mark.asyncio
async def test_order_refund_ledger(test_db, buyer_user, seller_user, approved_listing):
    order = Order(
        listing_id=approved_listing.id,
        buyer_id=buyer_user.id,
        seller_id=seller_user.id,
        current_state=OrderState.CREATED,
        item_price_paise=100000,
        shipping_fee_paise=0,
        commission_rate_bps=300,
        commission_paise=3000,
        seller_payable_paise=97000,
        total_buyer_paid_paise=100000
    )
    test_db.add(order)
    await test_db.commit()

    # Capture payment then refund
    await record_payment_captured_ledger(order, "pay_ref_1", test_db)
    await record_order_refund_ledger(order, "rfnd_gateway_1", test_db)

    # Balances should reset back to 0
    balances = {b["account_code"]: b["net_balance_paise"] for b in await get_account_balances(test_db)}
    assert balances["ASSET_ESCROW_NODAL"] == 0
    assert balances["LIABILITY_BUYER_FUNDS_HELD"] == 0

@pytest.mark.asyncio
async def test_daily_settlement_reconciliation_matched_and_mismatch(test_db, buyer_user, seller_user, approved_listing):
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()
    order = Order(
        listing_id=approved_listing.id,
        buyer_id=buyer_user.id,
        seller_id=seller_user.id,
        current_state=OrderState.CREATED,
        item_price_paise=250000, # ₹2,500
        shipping_fee_paise=0,
        commission_rate_bps=300,
        commission_paise=7500,
        seller_payable_paise=242500,
        total_buyer_paid_paise=250000
    )
    test_db.add(order)
    await test_db.commit()

    # Record payment capture today
    await record_payment_captured_ledger(order, "pay_recon_1", test_db)

    # 1. Gateway settlement report MATCHES ledger (₹2,500 reported)
    matching_settlements = [
        {"order_id": order.id, "gateway_amount_paise": 250000, "payment_id": "pay_recon_1"}
    ]
    matched_recon = await run_daily_settlement_reconciliation(today, matching_settlements, test_db)
    assert matched_recon.status == "MATCHED"
    assert matched_recon.discrepancy_paise == 0
    assert len(matched_recon.mismatches) == 0

    # 2. Gateway settlement report has MISMATCH (₹2,400 reported instead of ₹2,500)
    mismatched_settlements = [
        {"order_id": order.id, "gateway_amount_paise": 240000, "payment_id": "pay_recon_1"}
    ]
    flagged_recon = await run_daily_settlement_reconciliation(today, mismatched_settlements, test_db)
    assert flagged_recon.status == "MISMATCH_FLAGGED"
    assert flagged_recon.discrepancy_paise == -10000 # -₹100 mismatch
    assert len(flagged_recon.mismatches) == 1
