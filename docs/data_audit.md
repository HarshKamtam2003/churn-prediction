# Data Audit and Data Dictionary (Day 1)

## Audit notes

- Source file: `European_Bank.csv` (bank customer records)
- Size: 10,000 rows. 11 columns after cleaning (10 features + target).
- Missing values: none. Duplicate rows: none.
- Dropped columns: `CustomerId` and `Surname` (identifiers, no predictive value) and `Year` (value was 2025 for every row, so it carries no information). The file had no `RowNumber` column.
- Target: `Exited`. Churn rate is 20.4% (2,037 customers left, 7,963 stayed).
- Class imbalance: because only about 1 in 5 customers churn, accuracy is misleading. Models will be judged on recall, F1 and ROC-AUC.
- Clean file saved as `data/churn_clean.csv`.

## Data dictionary

| Column | Type | Meaning |
|---|---|---|
| CreditScore | Number | Customer's credit score; higher means more creditworthy |
| Geography | Category | Country of residence (France, Germany, Spain) |
| Gender | Category | Male or Female |
| Age | Number | Age in years |
| Tenure | Number | Years the customer has been with the bank |
| Balance | Number | Money held in the account |
| NumOfProducts | Number | Number of bank products held (accounts, cards, loans) |
| HasCrCard | 0/1 | 1 if the customer has a credit card |
| IsActiveMember | 0/1 | 1 if the customer actively uses the bank |
| EstimatedSalary | Number | Estimated yearly income |
| Exited | 0/1 | Target: 1 if the customer left the bank, 0 if they stayed |
