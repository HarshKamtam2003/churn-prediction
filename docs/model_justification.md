# Final Model Justification (Day 5)

## Decision

**Final model: XGBoost, decision threshold 0.29.** The model is locked; no further changes unless something breaks.

## Justification (draft for the paper)

XGBoost was selected because it had the highest cross-validated ROC-AUC (0.864) and the best test performance (ROC-AUC 0.871, F1 0.640 at the tuned threshold). It captured the non-linear patterns found in the exploratory analysis, such as the effect of the number of products held, that Logistic Regression (ROC-AUC 0.774) could not. It is also compatible with SHAP, which supports the explainability requirement. Lowering the decision threshold from 0.5 to 0.29 raised recall from about 49% to 68%, at the cost of lower precision.

## Model comparison (test set, default 0.5 threshold)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | CV AUC |
|---|---|---|---|---|---|---|
| Logistic Regression | 0.808 | 0.583 | 0.189 | 0.286 | 0.774 | 0.762 |
| Logistic Regression (balanced) | 0.714 | 0.388 | 0.708 | 0.501 | 0.777 | 0.765 |
| Decision Tree | 0.858 | 0.796 | 0.403 | 0.535 | 0.844 | 0.827 |
| Random Forest | 0.863 | 0.767 | 0.469 | 0.582 | 0.851 | 0.844 |
| Random Forest (tuned) | 0.865 | 0.791 | 0.457 | 0.579 | 0.862 | 0.858 |
| Gradient Boosting | 0.866 | 0.782 | 0.477 | 0.592 | 0.870 | 0.863 |
| **XGBoost** | **0.872** | **0.805** | **0.486** | **0.606** | **0.871** | **0.864** |

## Threshold trade-off (XGBoost, test set of 2,000 customers, 407 churners)

| | Default 0.5 | Chosen 0.29 |
|---|---|---|
| Precision | 0.805 | 0.607 |
| Recall | 0.486 | 0.676 |
| F1 | 0.606 | 0.640 |
| Churners caught (approx.) | 198 | 275 |
| False alarms (approx.) | 48 | 178 |

The threshold was chosen from cross-validated predictions on the training data only (the point that maximises F1), so the test set was not used to pick it. A higher threshold (for example 0.4) would cut false alarms if wasted retention offers are costly; this is a business decision.

## Other points

- Selection used cross-validated AUC, not test scores, to keep the test set unbiased.
- Cross-validation and test AUC are close (0.864 vs 0.871), so the result is stable.
- Random Forest overfit before tuning (train AUC 1.000 vs test 0.851); tuning reduced this.
- Figures: `reports/figures/14_roc_curves.png`, `15_precision_recall.png`, `16_final_confusion_matrix.png`.
- Saved model: `models/final_model.joblib` (pipeline, threshold and model name).
