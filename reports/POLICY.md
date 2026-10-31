> Historical v1 report. The active model is now v2; see HISTORY_REVISION.md for current results and economics.

# Step 4: dispatch policy and economics

Recommendation: pilot targeted, helpful confirmation calls without automatically delaying dispatch. Do not launch automatic holds. These are retrospective scenarios, not observed treatment savings or a production guarantee.

## Calculation and threshold

Policy v4.1 §4 gives Rs 1,150 return handling cost, excluding refund, and Rs 45 per completed confirmation call. §7 reports about 35% prevention in the call pilot, without sample size, uncertainty, randomization details or segment effects.

Expected handling-cost saving per completed call = predicted return probability × prevention effect × 1,150 − 45.

Break-even probability = 45 / (0.35 × 1,150) = 0.1118012422. Use the full precision value in software. Equality is financially neutral before overhead. This threshold comes from stated costs, not a search for the best holdout result. We retain the previously fixed calibrated score; raw-score comparison is disclosed only as sensitivity, not a reason to change the model after viewing holdout outcomes.

## Retrospective scenario: 2,126 holdout orders

| Policy | Completed calls assumed | Call cost | Returns prevented, expected | Net handling-cost saving versus ship normally |
|---|---:|---:|---:|---:|
| Ship normally | 0 | Rs 0 | 0 | Rs 0 |
| Call everyone | 2,126 | Rs 95,670 | 85.75 | Rs 2,942.50 |
| Call at risk ≥ 11.18% | 589 | Rs 26,505 | 49.35 | Rs 30,247.50 |

Unchanged baseline return handling cost = 245 × 1,150 = Rs 281,750. Targeted calling has 141 historical returns among 589 selected orders (23.94% precision; 57.55% recall). 448 selected orders did not return. The predicted probability is not an accusation or certainty. Expected 49.35 prevented returns is an average across hypothetical repetitions, not a literal fractional customer.

For the targeted policy: avoided handling cost = 141 × 35% × 1,150 = Rs 56,752.50. Subtract Rs 26,505 call cost. We do not count an entire refunded order value as profit saved; sale value is not contribution margin. Margin recovery, call-induced cancellations, attempts that do not connect, overhead, complaints, and repeat-customer value are unmeasured. Do not describe this as complete P&L impact.

Raw-score sensitivity at the same threshold selects 735 orders and estimates Rs 33,337.50 savings. This exposed holdout comparison is not an independent validation of choosing the raw model.

## Sensitivity: keep the same 589-order queue

| Prevention effect | Net savings |
|---|---:|
| 0% | −Rs 26,505 |
| 10% | −Rs 10,290 |
| 20% | Rs 5,925 |
| 35% | Rs 30,247.50 |
| 50% | Rs 54,570 |

This historical queue breaks even at 16.35% prevention, conditional on observed labels and Rs 45/1,150 costs. The individual probability threshold and queue-level break-even effect answer different questions. If the assumed intervention effect changes before deployment, recalculate the threshold rather than claiming these fixed-queue scenarios optimize it.

All selected calls are assumed completed. With a completion fraction q independent of return risk, zero attempt overhead and no harm, both benefits and completed-call costs scale by q. Real completion may depend on risk; log attempted/completed contacts separately. The source does not establish that its historical labels represent a no-call counterfactual, another limit on interpretation.

## Why holds cannot be approved from this analysis

The policy reports 12% cancellation among orders held over 24 hours. It does not establish the incremental cancellation effect, how cancellations relate to latent return risk, the prevention effect of a hold, contribution margin, handling cost of a hold, or lifetime-value impact. The call pilot's 35% must not be assigned to holds as evidence.

economics.json contains illustrative hold scenarios only. If 12% is assumed incremental and independent of return propensity, holding the selected 589 orders gives 70.68 expected cancellations. Let h be prevention among orders that do not cancel and M be margin lost on an otherwise-kept order:

Net before hold overhead and lifetime-value loss = 141 × (0.12 + 0.88h) × 1,150 − 448 × 0.12 × M.

This formula accounts for avoided handling on would-return cancellations without also charging kept-sale margin to those same orders. It is a simplified scenario, not an identified causal model. At h=0 and M=Rs 600 it loses Rs 12,798; at h=10% and M=Rs 1,000 it loses Rs 20,032.80. The arbitrary scenario margins and effects are NOT measured Kestrel values. No reliable single hold-profit estimate or hold threshold is available.

## Shield and channels

Current Shield snapshot: 478 holdout orders, 144 selected; 54 of these returned. Non-Shield: 1,648 orders, 445 selected; 87 of these returned. At the common 35% effect, scenario savings are Rs 15,255 for Shield and Rs 14,992.50 otherwise. Selection rates are 30.13% and 27.00% respectively. These do not establish equal treatment benefit or historical membership: the reference file lacks effective dates. Do not deny free-return entitlements or introduce a Shield-specific hold. Use current membership for live service etiquette and stratified monitoring.

Channel-level figures are provided in economics.json. All use the same assumed treatment effect, which remains unverified within each channel and group.

## Next-week pilot proposal

1. Confirm operational return horizon, contribution margins, caller capacity, contact preferences and the accounting definition of completed calls. Preserve current dispatch promises and Shield entitlements.
2. Freeze model, calibration and threshold version before enrollment. Run in shadow mode first to measure queue size, missing inputs and call reachability. No automatic holds.
3. Among eligible flagged customers, randomize by customer into call offer or business-as-usual groups, balancing current Shield membership and channel. Customer-level assignment avoids repeat orders receiving conflicting treatments. Follow contact preferences through the operational system; raw notes are not model instructions.
4. Log assignment before contact, order score, attempted/completed calls, dispatch delay, cancellation, return, handling cost and complaint. Analyze by assigned group, including unsuccessful calls, to avoid bias from selecting only reachable customers.
5. Set sample size and duration from the expected return reduction, desired precision and available traffic before starting; the pack cannot support a definitive sample-size claim. Wait for a complete agreed return window. One week starts the pilot; it does not prove savings.
6. Review actual incremental costs and outcomes, with uncertainty, by channel and Shield status. Stop any workflow that violates promised dispatch or customer entitlements. Expand only if evidence supports net benefit and acceptable customer impact.

## Reproduction and checks

Run `python3 src/economics.py --input-dir /path/to/data-pack` after training. Uses only local holdout predictions and customer reference data. No new fitting, threshold sweep or unlabelled test scoring occurs. Verified: selected counts reconcile, subgroup savings sum to total, call costs equal completed calls × 45, expected prevention never exceeds selected returns, and the scenario arithmetic matches independently computed totals.
