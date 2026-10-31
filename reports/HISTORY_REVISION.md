# History investigation and v2 revision

## What changed

The active model is kestrel-history-v2. It uses earlier order and return counts, removing redundant rate/no-history inputs. It was refitted through February 2026 (7,635 orders); the previous calibration was not reused on a different fitted model. All candidates used raw probabilities under the new predeclared development protocol. Numerical score changes reflect feature simplification, additional training observations and removal of calibration; they cannot be attributed to one cause alone.

Manual review is required when prior counts, quantity, discount, amount or promised days fall outside the observed fitting range. Ten earlier orders exceeds the maximum of nine. The UI withholds the headline percentage in this case; the API retains the diagnostic score and explicit manual-review recommendation. Min/max checks are a basic guard, not proof that every in-range combination is reliable. Dates after the evaluated period retain a warning. No automated actions occur.

## Investigation

Before March 2026, observed return rates were 8.88% for no prior orders (2,118 observations), 10.01% for 1–2 (4,306), and 21.06% for 3–9 (1,211). Increasing rates also appear within the current Shield snapshot groups. Family breakdowns and support counts are in history_segments.json. These descriptive comparisons do not hold other variables or prior returns constant, establish causality, or verify historical Shield status.

The original fitted order-count coefficient was +0.1147 per order before calibration; v2 is +0.0224. The positive association remains, so more successful purchases do not mechanically force a lower score. We did not impose that behavior merely to make one example look plausible.

## Development evidence

Fixed folds: fit before July 2025 → August; before September → October; before November → December; before January 2026 → February. One whole-month gap precedes each evaluation window. Smoothing strength was fixed at five pseudo-orders with a prior estimated from each fitting portion only. No future labels enter preprocessing. Development observations total 2,762.

| History representation | Pooled development log loss (lower better) |
|---|---:|
| Original four inputs | 0.311978 |
| Counts only (selected) | 0.311745 |
| Return rate and no-history flag | 0.324823 |
| Smoothed return rate and no-history flag | 0.315519 |
| Smoothed rate, log successful orders and no-history flag | 0.312060 |

The improvement over the original is tiny; no statistically established major accuracy gain is claimed. The simpler model wins the declared criterion, not a desire to lower the screenshot's prediction. This investigation was prompted by an exposed evaluation/model behavior, so the entire revision is exploratory rather than a newly independent confirmatory study.

## Previously exposed holdout: diagnostic only

April–June 2026: AUC 0.7552; average precision 0.3725; Brier 0.08807; log loss 0.30577. Old calibrated model: 0.7530, 0.3733, 0.08833, 0.30869 respectively. Mixed small differences do not establish a robust improvement. This period was not used to select v2, but had already been inspected; do not call it a fresh blind test. New labelled orders or a controlled prospective pilot are needed for stronger evidence.

## Current economics

Using the same cost-derived threshold and excluding one out-of-range holdout order: 645 selected calls, 148 historical returns among those selected, Rs 29,025 call cost, 51.8 expected prevented returns and Rs 30,545 estimated net handling savings at the assumed 35% prevention effect. Break-even effect for this retrospective queue is 17.05%. These are scenarios, not observed intervention results. Updated details are in economics.json; POLICY.md is retained as historical v1 documentation.

## Verification and reproduction

Run src/revise_history.py with the analysis dependencies, then src/economics.py with the source pack. The former writes the active model JSON and private diagnostic predictions; it does not use test outcomes. The protocol and full fold results are saved alongside this report. Original model and economics were retained under reports/v1; original holdout scores are in data/holdout_predictions_v1.csv.

Nine automated tests passed including a new out-of-range history test. Portable scoring matches the refitted sklearn model across all 12,600 supplied orders, maximum absolute difference 2.22e-16. Two historical records and zero unlabelled test records trigger the current range guard. This proves implementation agreement, not predictive accuracy. UI verification checks the ten-order example displays manual review instead of a confident headline percentage.
