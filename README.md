# Kestrel Returns Risk

A working application that estimates whether an appliance order will be returned before dispatch. Employees receive a risk estimate, readable model factors, and a suggested next step.

**Python 3.10+ · No runtime dependencies · No paid API key · 2,096 submission predictions**

[Evaluation evidence](EVIDENCE.md) · [Business memo](MEMO.md) · [Predictions](predictions.csv) · [Automated tests](https://github.com/Kartik-loop/kestrel-returns-risk/actions/workflows/tests.yml)

> This is a locally runnable evaluation prototype. It does not automatically hold shipments or make calls. The evidence does not establish 95% accuracy.

## How it works

```text
Order form → JSON endpoint → Input validation → Saved logistic regression model
                                                     ↓
                                  Risk + reasons + warnings + recommendation
```

The interface and batch predictions use the same frozen `kestrel-history-v2` model. No external AI service is called when an order is scored.

## Quick start

Requires Python 3.10 or newer. No packages or paid API key are needed.

Download and extract the repository ZIP, or clone it with your authorized GitHub account:

```sh
git clone https://github.com/Kartik-loop/kestrel-returns-risk.git
cd kestrel-returns-risk
```

From the extracted or cloned repository folder:

```sh
python3 src/server.py
```

Open **http://127.0.0.1:8000/** in your browser. Keep the terminal running while using the app; stop with **Ctrl+C**.

On Windows, use `py -3 src/server.py` if `python3` is unavailable.

### If the page does not open

The browser address must match the port printed in the terminal. For example, to use port 8002:

```sh
python3 src/server.py --port 8002
```

Then open **http://127.0.0.1:8002/**.

| Problem | What to do |
|---|---|
| Connection refused | Start the server and leave its terminal open; check the port in the address. |
| Address already in use | Choose another port with `--port`, then open that same port. |
| Cannot find `src/server.py` | Open a terminal inside the extracted repository folder. |
| Model unavailable | Ensure `assets/model.json` is present, then restart the server. |
| Cannot access the repository | Request access from the owner; this is a private engagement repository. |

`127.0.0.1` means your own computer. GitHub stores the project files; it does not host the running Python application. Each evaluator can run their own copy without the author's computer being online.

The local server receives one order at `POST /api/predict` and returns its estimated risk, model factors, warnings and suggested action. The screen calls this endpoint. It performs no calls or automatic dispatch holds, and stores no requests.

## Deliverables

| File | Purpose |
|---|---|
| `src/`, `web/`, `assets/model.json` | Runnable service, screen and frozen model |
| `predictions.csv` | 2,096 scores, in the supplied template order |
| `MEMO.md` | Business decision, numbers, rupees and next steps |
| `EVIDENCE.md`, `reports/` | Current evaluation evidence and release hashes |
| `tests/test_service.py` | Eleven automated service checks |

The original data pack, raw customer records, local environments, development logs and obsolete model versions are excluded. This final submission contains inference code. Training scripts, experiments and earlier reports remain available in the repository history at commit `fdf6103`; the final model and predictions are unchanged.

## Demonstration

1. Reset the form to the invented sample and select **Review return risk**: approximately **11.0%**.
2. Keep earlier orders at three and change earlier returns to three: approximately **46.8%**, with a confirmation-call suggestion.
3. Change earlier orders to eleven: manual review, with no risk percentage.
4. Reset the sample when finished.

These examples demonstrate behavior, not predictive accuracy. Other valid inputs outside observed ranges receive provisional scores and no financial estimate.

Training history reaches only nine earlier orders, and quantities one or two. The above-ten review boundary is a configured operating preference, not a proven accuracy boundary. Newer dates receive a warning. Invalid inputs are rejected.

## Results and limitations

| Measure | Result |
|---|---:|
| Distinct historical orders | 10,504 |
| Historical returns | 1,200 (11.42%) |
| Development ROC AUC | 0.7664 |
| Diagnostic ROC AUC | 0.7552 |
| Diagnostic average precision | 0.3725 |
| Submission orders | 2,096 |

10,504 distinct historical orders included 1,200 returns (11.42%). Logistic regression with counts-only purchase history was selected across four chronological development windows. Development AUC was 0.7664; the already-exposed April–June diagnostic AUC was 0.7552. AUC is not accuracy. These results do not establish 95% accuracy or fresh independent final-test performance.

The call threshold is `45 / (0.35 * 1150)`, approximately 11.18%. The ₹30,545 retrospective savings scenario assumes 35% prevention and applies only to supported inputs. It is not observed intervention savings. See [evidence](EVIDENCE.md) and [memo](MEMO.md).

## Data preparation and model choice

- Reconciled 651 duplicate imports before modelling.
- Corrected 700 October 2025 amounts only after confirming a 100× unit discrepancy against catalog price, quantity and discount.
- Excluded post-return pickup/service data and unverified historical customer snapshots.
- Treated instructions inside customer notes as untrusted data; notes are not predictors.
- Compared logistic regression with boosted trees, then compared five purchase-history representations across four chronological development windows.
- Selected the counts-only history representation by development log loss. Its improvement was small; no major accuracy gain is claimed.

The model learns associations from order details. A customer's past return fraction is one description of their history, not the probability of every future order. Displayed reasons are grouped mathematical contributions, not causal explanations or percentage-point changes.

## JSON endpoint

Send one order to `POST /api/predict` with `Content-Type: application/json`:

```json
{"order_id":"DEMO-001","order_placed_at":"2026-09-15 10:30","sku":"KH-AF-01","sales_channel":"web","payment_mode":"prepaid_upi","discount_pct":10,"qty":1,"order_value_inr":4679.10,"promised_delivery_days":5,"delivery_pincode":"411001","is_gift":"N","customer_prior_orders":3,"customer_prior_returns":1}
```

The response contains `score`, `reasons`, `recommendation`, `warnings`, `model_version` and `action_executed: false`. Manual-review cases return a null score. Dates are IST, pincode is a six-digit string, and amount must agree with catalog price, discount and quantity. Extra fields are ignored; post-return data never affects scoring. Catalog: `GET /api/catalog`. Readiness: `GET /api/health`.

## Verify

```sh
python3 -m unittest discover -s tests -v
```

Tests check validation, score behavior, ignored leakage fields, recommendation boundaries and HTTP routes. Software correctness is distinct from predictive accuracy.

To regenerate predictions with the original files (not included):

```sh
python3 src/predict_batch.py --input /path/to/test_unlabelled.csv --template /path/to/sample_submission.csv
```

This uses the same frozen model as the screen and overwrites `predictions.csv` and the release manifest. Use actual supplied filenames, including UUID prefixes where present.

## Expected hidden-test performance

Before external submission, the provisional expectation is ROC AUC around 0.75 and average precision around 0.37, anchored to chronological development and the already-exposed diagnostic period. This is not a guarantee or confidence interval. Drift, label maturity and different test prevalence can change performance. The hidden scoring metric has not been specified.

## AI disclosure

Codex assisted with inspection, cleaning, model experiments, implementation, tests and documentation. The user reviewed behavior and prompted the history and manual-review revisions. The application itself uses no LLM or paid model API. Exact assistant subscription or usage charges are unavailable; no per-order model API charge is incurred.

Discarded approaches include post-return predictors, accuracy-only evaluation, automatic holds, redundant history features and alternatives that did not improve the development criterion.

## Submission status and sharing

The actual screen recording (maximum three minutes, no slides) and external submission form remain separate tasks. This repository is not a substitute for either.

This repository remains private under §10 of the supplied operations policy. Grant authorized evaluators repository access before submitting the link. The video and submission form are still outstanding; no video or form completion is claimed.
