# AI-use disclosure

Codex assisted with source-file inspection, data preparation, model experiments, interpretation, Python/HTML/CSS/JavaScript implementation, tests, documentation and submission packaging. The user reviewed results and identified counterintuitive customer-history behavior and unclear manual-review output, prompting further investigation and changes.

The product does not call an LLM or paid model API. Scores come from fitted logistic regression; reasons come from grouped coefficient contributions. No per-order model API charges are incurred. Local compute, human effort and any Codex subscription/usage costs are not zero; exact Codex account charges are unavailable and are not invented here.

Rejected/changed approaches: post-return pickup/service inputs, instructions embedded in notes, using accuracy alone, automatic holds, the original redundant history representation, and history-rate alternatives that did not improve the development criterion. The current service uses raw v2 probabilities; it does not reuse v1's calibration transform.

The supplied data was processed locally. No public repository or hosted site was created. A small official scikit-learn documentation lookup supported metric explanations; training and scoring did not require a remote model service.
