# Current release summary

Model: kestrel-history-v2, logistic regression fitted through February 2026, with raw probabilities. Weights are frozen and identical to the app used for submission scoring. Service review rule: earlier orders >10 requires manual review; otherwise valid out-of-range inputs display provisional scores without financial estimates. No actual calls or holds are performed.

Data: 11,155 historical rows reduced to 10,504 unique orders, including 1,200 returns. 700 October amounts corrected after reconciliation. Post-return event fields excluded. Instructions inside notes ignored. Current customer membership snapshots excluded as predictors. All 2,096 submission records have finite scores and exact template IDs/order.

Four chronological development windows and five history representations selected counts-only by lowest pooled log loss (0.311745), a tiny improvement over the original representation (0.311978). Development AUC 0.7664, average precision 0.3760. The already-exposed April–June diagnostic period has AUC 0.7552, average precision 0.3725, Brier 0.08807 and log loss 0.30577. This does not establish 95% accuracy or robust superiority. The holdout is not freshly independent after iterative development.

The supported-input pilot scenario selects 645 of 2,126 diagnostic orders, including 148 historical returns. At assumed 35% prevention: Rs 29,025 call cost, Rs 59,570 avoided handling, Rs 30,545 net handling savings. One out-of-range case was excluded from this analysis. Do not apply that benefit estimate to newly permitted extrapolated inputs. No hold-effectiveness or contribution-margin evidence establishes a profitable holding policy.

Proposed next step: customer-randomized, supported-input confirmation-call pilot preserving dispatch promises and Shield entitlements. Measure mature outcomes, costs and complaints before expansion.

Known limitations: uncertain return observation horizon and point-in-time labels; unversioned reference data; temporal drift; narrow training ranges; no proven intervention effect by segment; no fully independent v2 final test. Predictions are estimates, not guaranteed outcomes.

The service calculation matches sklearn within floating-point precision across 12,600 supplied records. This is implementation verification, not proof of predictive accuracy. See release_validation.json for package checks.
