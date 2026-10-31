# Audit findings and dispatch feature contract

## Step 1: evidence and cleaning

- 11,155 training rows become 10,504 unique orders. Each of 651 duplicate pairs differs only in source. Keep CRM copy after verifying all other fields agree; fail on conflicting duplicates. Test has 2,096 unique orders.
- There are 1,200 returned orders: 11.4242%. Always predicting no return gives 88.5758% accuracy and zero recall. This is a baseline, not a useful model.
- All reference keys are unique, every order joins to both references, train/test order IDs do not overlap, and test IDs and sequence match the submission template.
- All 700 unique October 2025 orders have stored amount equal to 100 times list price × quantity × (1 − discount/100). Other months reconcile without conversion. Divide only October 2025 records whose corrected amount matches within 0.011 rupees. Preserve raw amount and correction flag. This is an evidence-based unit correction, not confirmation of the gateway's implementation. Future unexplained mismatches must fail review rather than receive an automatic blanket correction.
- 1,999 training orders and 18 test orders precede customer signup. Do not manufacture signup dates or negative tenure. Exclude signup and tenure from the baseline; preserve the issue log. No orders precede product launch.
- Default pincode 000000 occurs in 848 training and 176 test orders, including non-partner channels. Treat as unknown address, never as a geographic location. Do not infer walk-in status solely from it. Pincodes stay strings in clean data; model uses only address_missing.
- Four unique training notes contain instructions addressed to analysts or automated tools. These are untrusted content and were not followed. Detection is a simple diagnostic, not an exhaustive security classifier. Exclude all free text and note-derived predictors from baseline; preserve originals privately. Do not drop the affected orders or use the diagnostic flag as a predictor.
- Validate quantities, discounts, history bounds, label values, pincode shape, dates and price reconciliation during preparation. Missing-value counts are recorded after deduplication in audit.json. Missing note/pickup values are not filled with invented events.
- Training covers 2025-04-01 through 2026-06-30; test covers 2026-07-01 through 2026-09-30. Historical event types differ fundamentally from dispatch snapshot event types: test has NONE and INSTALL_BOOKED; train includes completed service and reverse pickups.

## Step 2: feature contract

Decision moment: immediately before dispatch. One row is one order. Target: supplied returned flag; the pack does not define its complete observation horizon or export timestamp. Do not relabel it as a proven 30-day outcome. Label maturity, particularly near the training cutoff, remains an evaluation limitation.

### Baseline predictor allowlist

sku, sales_channel, payment_mode, discount_pct, qty, order_value_inr (corrected), promised_delivery_days, is_gift, customer_prior_orders, customer_prior_returns, prior_return_rate, no_prior_orders, address_missing, family, list_price_inr, product_age_days, order_month, order_weekday, order_hour.

- Historical counts are documented as prior to this order; rely on that definition provisionally. Do not recompute them from future rows. prior_return_rate is prior_returns/prior_orders; use 0 with a separate no_prior_orders flag when denominator is zero.
- Calendar fields use the supplied order timestamp in IST. Do not apply the policy's legacy resolution-event UTC conversion to order timestamps. There is no resolution-event timestamp field to repair here.
- Product reference attributes are treated as catalog facts known at order time. Launch dates are consistent. Historical list prices are not independently versioned, although all order amounts reconcile after the documented correction. This assumption must be disclosed.
- No target-dependent encodings, imputers, category vocabularies or scaling are fitted in these steps. Fit any learned preprocessing only on the training portion during step 3.

### Retain as metadata, never feed to the estimator

order_id: submission join and traceability. customer_id: customer overlap and subgroup diagnostics. order_placed_at: chronological splitting. returned: training target only, absent in test.

### Excluded from baseline

| Field | Reason |
|---|---|
| pickup_scheduled_at | Created after return approval; unavailable at decision time, even though bookings can be cancelled |
| last_service_event_type | Export-time state includes events after dispatch; no historical as-of event timestamps |
| source | Import provenance and duplicate processing; all retained rows are CRM |
| delivery_note and derived text signals | Untrusted instructions, access codes, possible edits and unverified historical availability |
| delivery_pincode as exact location | Sparse exact location and default semantics; retain only missing-address indicator |
| signup_date / customer tenure | Thousands of chronology inconsistencies |
| shield_member | Current reference snapshot; no membership effective dates. Retain for descriptive/sensitivity work with caveat, not default predictor |
| customer city/state | Current profile may have changed; no historical snapshots |
| warranty_months | Catalog entitlement versus Shield extension needs separation; defer |
| model_name | Redundant with SKU and family |
| raw amount and correction/issue flags | Data-processing artifacts, not customer-risk signals |

No automatic hold is authorized by these files or implemented. A score predicts association, not whether an intervention causes improvement. Cost policy and the call pilot will inform step 4, with uncertainty and cancellation-margin assumptions explicit.

## Learning sequence

1. Establish the unit of observation before counting outcomes: duplicate orders distort training and evaluation.
2. Reconcile numbers against an independent identity before changing units. A high value alone is not evidence of an error.
3. Draw the timeline: order → dispatch decision → delivery/service → return request → reverse pickup. Only information known at the decision may enter the predictor.
4. Separate a clean investigation table from a strict predictor table. Keeping a column for audit does not authorize using it for prediction.
5. Split by time in the next step, keeping duplicate order IDs together. Evaluate customer overlap and new-customer behavior. Do not randomly mix future and past or tune on final holdout results.
6. Freeze the outcome window assumption and latest holdout before comparing models. Assess label maturity and reserve a gap if the documented/assumed outcome window requires it. We have not yet selected or evaluated models.

## Verification performed

Preparation completed successfully on the supplied pack. The pipeline checks duplicates, reference uniqueness, joins, overlap, submission order, numeric bounds, date parsing, labels and amount reconciliation. All generated train/test feature schemas match except the training target. Excluded raw fields are absent from predictor tables. Original file SHA-256 hashes are recorded for reproducibility. Inputs are never written by the pipeline.
