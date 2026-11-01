# Kestrel Returns Risk

Minimal submission: a local pre-dispatch return-risk service, employee screen, frozen model, predictions, business memo and evaluation evidence.

## Run

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

Open http://127.0.0.1:8000. If the port is occupied, run `python3 src/server.py --port 8080` and open http://127.0.0.1:8080. Keep the terminal running while using the app; stop with Ctrl+C. The port in the browser must match the startup command. `127.0.0.1` refers to your own computer, not a hosted website. Windows users may use `py -3` instead of `python3`.

The local server receives one order at `POST /api/predict` and returns its estimated risk, model factors, warnings and suggested action. The screen calls this endpoint. It performs no calls or automatic dispatch holds, and stores no requests.

## Deliverables

| File | Purpose |
|---|---|
| `src/`, `web/`, `assets/model.json` | Runnable service, screen and frozen model |
| `predictions.csv` | 2,096 scores, in the supplied template order |
| `MEMO.md` | Business decision, numbers, rupees and next steps |
| `EVIDENCE.md`, `reports/` | Current evaluation evidence and release hashes |
| `tests/test_service.py` | Eleven automated service checks |

The original data pack, customer records, local environments, development logs and obsolete model versions are excluded. This final submission contains inference code. Training scripts, experiments and earlier reports remain available in the repository history at commit `fdf6103`; the final model and predictions are unchanged.

## Demonstration

Reset the invented example: about 11.0% risk. Keep three earlier orders and change earlier returns to three: about 46.8%. More than ten earlier orders produces manual review without a score. Other valid inputs outside observed ranges receive provisional scores and no financial estimate.

Training history reaches only nine earlier orders, and quantities one or two. The above-ten review boundary is a configured operating preference, not a proven accuracy boundary. Newer dates receive a warning. Invalid inputs are rejected.

## Evidence and limitations

10,504 distinct historical orders included 1,200 returns (11.42%). Logistic regression with counts-only purchase history was selected across four chronological development windows. Development AUC was 0.7664; the already-exposed April–June diagnostic AUC was 0.7552. AUC is not accuracy. These results do not establish 95% accuracy or fresh independent final-test performance.

The call threshold is `45 / (0.35 * 1150)`, approximately 11.18%. The ₹30,545 retrospective savings scenario assumes 35% prevention and applies only to supported inputs. It is not observed intervention savings. See [evidence](EVIDENCE.md) and [memo](MEMO.md).

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
