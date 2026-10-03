# EDA Findings (Day 2)

1. Overall churn is 20.4% (2,037 of 10,000 customers), so the data is imbalanced.
2. Churn rises sharply with age: 7.5% (18-30), 12.1% (31-40), 34.0% (41-50), 56.2% (51-60), then falls to 24.8% (60+).
3. Germany has about double the churn of France and Spain (32.4% vs 16.2% and 16.7%).
4. Women churn more than men (25.1% vs 16.5%).
5. Customers holding 3 or 4 products almost always leave (82.7% and 100%), but they are rare: 326 customers, about 3.3% of the bank.
6. Holding 2 products is the safest position (7.6% churn); holding 1 product gives 27.7%.
7. Inactive members churn nearly twice as much as active ones (26.9% vs 14.3%).
8. Having a credit card (20.2% vs 20.8%), tenure (about 20% in every year) and salary make almost no difference.
9. Customers with a zero balance churn less (13.8%) than those with a balance (24.1%), the opposite of the initial expectation.
10. Age (+0.29) and activity status (-0.16) have the strongest correlations with churn. Outliers in Age and CreditScore are valid values and are kept.

## Top 5 highest-churn groups

| Rank | Group | Churn rate | Customers |
|---|---|---|---|
| 1 | 4 products | 100% | 60 |
| 2 | 3 products | 82.7% | 266 |
| 3 | Age 51-60 | 56.2% | n/a |
| 4 | Age 41-50 | 34.0% | n/a |
| 5 | Germany | 32.4% | n/a |

## Notes

- NumOfProducts looks weak in the correlation heatmap (-0.05) because its effect is not a straight line, which supports using tree-based models.
- Figures are in `reports/figures`.
