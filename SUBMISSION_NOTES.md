# Submission preparation — not a completed external form

Private repository: https://github.com/Kartik-loop/kestrel-returns-risk. The actual submission form has not been supplied. No external form has been submitted or video recorded.

## Expected performance, recorded before external submission

The brief does not specify the hidden scoring metric. A provisional expectation for the same return-label definition is ROC AUC around 0.75 and average precision around 0.37, anchored to chronological development and the already-exposed April–June diagnostic period. This is a planning estimate, not a guarantee or an independently validated confidence interval for test performance. Expect roughly high-80s accuracy at a 50% cutoff; 95% is unsupported. Different test prevalence, temporal drift, label maturity and the exploratory revision may materially change these numbers.

Final v2 development pooled AUC: 0.7664; average precision: 0.3760; log loss: 0.31175. Exposed holdout diagnostic AUC: 0.7552; average precision: 0.3725; Brier: 0.08807; log loss: 0.30577. Do not represent these as hidden-test outcomes. The v1 confidence intervals do not automatically apply to v2.

## Before sending

- Grant the authorized evaluators access to the private repository; the data policy prohibits public sharing. Do not publish the original pack.
- Commit the contents of this package, including predictions.csv at repository root. It is not git-ignored.
- Run README startup and tests.
- Record the demo using RECORDING_SCRIPT.md, at most three minutes and no slides.
- Complete the actual form with repository/video links, expected metric and rationale, AI disclosure, and any identity fields requested.
- Confirm evaluator access. The form and recording are still required; this ZIP alone is not a complete external submission.
