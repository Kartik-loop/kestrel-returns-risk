# Screen-recording guide — target 2 minutes 45 seconds

This is a script, not an actual recording. Record your screen using the working app and repository files; no slides. Rehearse and keep the final recording under three minutes.

**0:00–0:25 — Start the service.** Show README startup and the screen. “This is a local dispatch-risk tool. It runs with Python alone, without a paid API. It returns a score, model factors and a provisional action; it never holds an order.”

**0:25–1:00 — Show two supported examples.** Reset the sample. Review the default order (about 11.0%). Change earlier returns from one to three, keeping earlier orders at three. Review again (about 46.8%). “These are associations learned from historical data, not certain outcomes or causal explanations.”

**1:00–1:25 — Show the limitation.** Set earlier orders to eleven. Show manual review. “We found the training history only reached nine prior orders. The configured demo review boundary is above ten. Other unusual inputs are explicitly provisional, with no savings estimate. I do not claim their accuracy is validated.” Reset the sample afterwards.

**1:25–2:00 — What changed and what was discarded.** Show reports/DECISIONS.md and HISTORY_REVISION.md. “I reconciled duplicate imports and October amounts, excluded post-return pickup/service fields, and ignored instructions embedded in notes. I compared logistic regression with boosted trees. After discovering unexpected history behavior, I tested five history representations across four chronological development windows. Counts-only won narrowly; smoothed rates did not improve the criterion. I did not force weights to fit one example.”

**2:00–2:30 — Evidence and business choice.** Show SUMMARY.md and MEMO.md. “95% accuracy is not supported. The revised holdout was already exposed, so I label it diagnostic. Targeted calls have conditional estimated savings of Rs 30,545 on supported holdout inputs at 35% prevention. A controlled pilot must establish actual benefit. Automatic holds lack evidence.”

**2:30–2:45 — Deliverables.** Show root predictions.csv, README and tests. “All 2,096 submission IDs are present in template order. The predictions use the same frozen model as the service. AI assistance and limitations are disclosed.”
