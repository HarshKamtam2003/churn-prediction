# Churn Drivers and Retention Recommendations (Day 6)

Model: XGBoost, decision threshold 0.29. Explanations use SHAP on the 2,000-customer test set.

## Why a specific customer was flagged (checkpoint)

**Customer:** 58-year-old male in Germany, 4 products, inactive member, balance 133,746 on an estimated salary of 28,374. Predicted churn risk 0.995. The customer did leave.

| Factor | Effect on risk (log-odds) |
|---|---|
| Holds 4 products | +3.07 |
| Age 58 | +1.72 |
| Inactive, so engagement x products = 0 | +0.52 |
| Lives in Germany | +0.39 |
| Product density (products per year of tenure) | +0.32 |
| Balance very high relative to salary | +0.26 |

The model starts from an average log-odds of -1.37 (about 20% risk) and these factors push it up to 5.25 (about 99.5%). Holding 4 products and being in the 50s drove most of it.

**Contrast cases**
- Near the threshold (risk 0.29): a 61-year-old woman in Spain with 1 product who is an active member. Age pushes risk up (+1.20), being active with a product pulls it down (-0.73). She did not leave.
- Lowest risk (0.009): a 26-year-old man in France with 2 products who is active. Holding 2 products (-1.15) and being young (-0.88) drive the low score.

## Top drivers in plain language

| Driver | Evidence | Plain statement |
|---|---|---|
| Age | SHAP rank 1; partial dependence rises to a peak in the 50s, then falls | Customers aged 45-60 churn about 5.0 times as often as those under 40 |
| Number of products | SHAP rank 2; partial dependence: 1 product about 27%, 2 about 11%, 3 about 75%, 4 about 83% | Customers with 3-4 products churn about 11.3 times as often as those with 2 |
| Activity | Churn 26.9% inactive vs 14.3% active; effect shared between IsActiveMember and EngagementProduct | Inactive members churn about 1.9 times as often as active members |
| Geography | SHAP rank 4 | Customers in Germany churn about 2.0 times as often as those in France or Spain |
| Gender | SHAP rank 5 | Women churn about 1.5 times as often as men |

Balance on its own has almost no effect (partial dependence is flat near 20%).

## Logistic Regression vs SHAP

- Direction agrees for 13 of 16 features. The three that differ (EngagementProduct, ProductDensity, Tenure) are engineered or minor features.
- Both put Age, Germany and Gender in their top 5.
- **NumOfProducts:** SHAP rank 2, Logistic Regression rank 8. The effect is not a straight line (2 products is safest, 3-4 is riskiest), which Logistic Regression cannot represent.
- **IsActiveMember:** Logistic Regression rank 1, SHAP rank 9. XGBoost splits the activity effect between IsActiveMember and EngagementProduct, so the single bar understates it.
- Age is spread over Age, AgeTenure and AgeByTenure, so its true influence is larger than one bar shows.

## Retention recommendations

1. **Age 45-60: proactive relationship outreach.** Highest-risk age group (5.0 times the under-40 rate). Offer a relationship-manager call and products suited to this stage of life.
2. **Customers with 3 or more products: service and fee review.** Rare (about 3% of customers) but 83-100% churn. Check for fees, complexity or service problems before they leave.
3. **Inactive members: re-engagement campaign.** Prompts to use the app or card, reminders of benefits, and a follow-up for those who stay silent.
4. **Germany: local investigation.** Churn is double the other countries. Review pricing, service quality and local competition.
5. **Single-product customers: test moving to a second product.** Two-product customers churn least (7.6%). This is an association, so test it with a pilot group before rolling it out.

Practical use: customers scoring above 0.29 form the retention-call list, and the SHAP explanation tells the agent which issue to address.

## Caveats

- These are associations in the data, not proven causes. Test recommendations with a pilot before wide rollout.
- Gender is a diagnostic here (are women's needs being met?), not a basis for treating customers differently.
- Figures: `reports/figures/17` to `23` (feature importance, SHAP beeswarm and bar, three waterfalls, partial dependence). Table: `reports/day6_logreg_vs_shap.csv`.
