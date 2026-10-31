> Historical v1 report. The active model is now v2; see HISTORY_REVISION.md for current results and economics.

# Step 3: chronological model evaluation

Status: evaluation complete; no production readiness claim. No unlabelled test outcomes used. Do not tune further against this exposed holdout and continue calling it untouched.

## Design

Training: April–September 2025. Model selection: November–December 2025. Calibration: February 2026. Final holdout: April–June 2026. October, January and March are provisional maturity buffers. Return outcome horizon and historical label availability remain unknown, so this is an approximate historical simulation, not proof of point-in-time labels.

Four fixed candidates were compared: constant prior, regularized logistic regression, and two boosted-tree configurations. Lowest selection log loss selects logistic regression. Selection log losses: constant 0.33489; logistic 0.29696; shallow trees 0.29775; medium trees 0.30236. The small gap between logistic and shallow trees is not evidence of universal superiority. Preprocessing is fitted only on the training window. Models use the step-2 allowlist; identifiers and targets are excluded.

A sigmoid probability adjustment was fitted on February only. Its use was fixed before holdout evaluation. We report both variants without choosing a winner from holdout results. The saved evaluation model remains fitted on the early training period; it has not been refitted on all available data for deployment.

## Holdout: 2,126 orders, 245 returns

| Metric | Constant baseline | Logistic raw | Logistic calibrated |
|---|---:|---:|---:|
| ROC AUC | 0.5000 | 0.7530 | 0.7530 |
| Average precision | 0.1152 | 0.3733 | 0.3733 |
| Brier loss (lower better) | 0.10196 | 0.08827 | 0.08833 |
| Log loss (lower better) | 0.35733 | 0.30642 | 0.30869 |
| Accuracy at 50% cutoff | 88.48% | 89.23% | 89.28% |

Calibrated model at 50% cutoff: 34 true positives, 17 false positives, 211 false negatives, 1,864 true negatives. Precision 66.67%; recall 13.88%. This cutoff is descriptive, not the recommended business action threshold. 95% accuracy has not been achieved.

Calibration did not improve held-out Brier or log loss. The calibrated average risk is 10.28%, versus 11.52% actual returns. Raw average risk is 11.85%. A single calibration month offers limited evidence; do not claim well-calibrated probabilities based on these results alone. See calibration_bins.csv for reliability by risk range.

Monthly AUC: April 0.772, May 0.757, June 0.726. This warrants monitoring; it does not establish a statistically significant trend. AUC for customers absent from fit/selection/calibration is 0.756 (1,048 orders), versus 0.750 for previously observed customers (1,078 orders). These are exposure groups, not necessarily first-time Kestrel customers. Channel and monthly results are in model_results.json. Shield analysis remains for the policy stage and must disclose reference-snapshot limitations.

## Uncertainty

Customer-cluster bootstrap (500 repetitions, fixed seed), conditional on this fitted model and period:
- roc_auc: 0.7189–0.7844 (95% percentile interval)
- average_precision: 0.3104–0.4284 (95% percentile interval)
- brier: 0.0796–0.0994 (95% percentile interval)

These intervals do not include model-selection uncertainty, future drift, uncertain label maturity, or the causal effect of calling or holding orders.

## Learn the metrics

- ROC AUC measures ranking across cutoffs; 0.753 is not 75.3% accuracy.
- Average precision summarizes precision/recall as the cutoff varies; 0.373 is not the precision at every cutoff.
- Brier and log loss assess probability quality; both combine reliability and discrimination. A reliability table helps diagnose calibration separately.
- Precision asks: of those flagged, how many returned? Recall asks: of actual returns, how many did we flag?
- Calibration changes probabilities, not necessarily ranking. Here the monotonic adjustment leaves AUC and average precision unchanged.

Metric reference: https://scikit-learn.org/stable/modules/model_evaluation.html

## Reproduction and next step

Install requirements.txt in a local Python environment, run src/prepare.py, then run `python src/train.py`. Tested with the versions recorded in model_results.json. A clean-machine dependency installation was not verified: network installation failed, so evaluation used the existing local Anaconda environment. No paid API or data upload was used.

Private order-level predictions are under data/holdout_predictions.csv. models/evaluation_model.joblib is a local trusted pickle artifact; load only trusted model files. It is an evaluation artifact, not a final serving model. Experiment settings and data hash are in experiment_plan.json.

Next: choose the intervention using cost assumptions and sensitivity analysis. Treat resulting holdout economics as retrospective estimates, not causal proof. Validate policy and calibration prospectively before automatic dispatch actions. A final refit and any changed calibration procedure need a clearly documented validation strategy; do not silently transfer holdout metrics to a different final model.
