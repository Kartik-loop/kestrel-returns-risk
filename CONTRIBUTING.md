# Development notes

Keep this repository private and do not commit source customer/order data or credentials. Run `python3 -m unittest discover -s tests -v` before proposing changes. Changes to preprocessing or inference must be checked against the fitted model and submission output. Model changes require chronological development evidence and a new model/prediction manifest; do not repeatedly optimize against an already-exposed holdout. Clearly label assumed intervention effects and provisional extrapolations. No production deployment or automatic dispatch action is implemented.
