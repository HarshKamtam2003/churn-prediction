# Predictive Churn Intelligence for Retail Banking

A model and dashboard that predict which bank customers are likely to leave, give each customer a churn probability, and explain the main drivers, so a bank can contact the right customers before they go.

**Live dashboard:** https://bank-churn-data-model.streamlit.app

## Headline results

- Data: 10,000 retail bank customers; 20.4% churned (2,037 left, 7,963 stayed).
- Final model: tuned XGBoost. Test ROC-AUC 0.871 (cross-validated 0.864). Logistic Regression baseline: 0.774.
- Decision threshold 0.29, chosen from the precision-recall curve on training data only: precision 0.607, recall 0.676, F1 0.640.
- Accuracy alone is misleading here: a model that predicts "nobody leaves" is already about 80% accurate, so models were judged on recall, F1 and ROC-AUC.

## Main churn drivers

| Driver | Churn compared with the comparison group |
|---|---|
| Age 45-60 | 5.0 times those under 40 |
| 3-4 products held | 11.3 times those holding 2 products |
| Inactive members | 1.9 times active members |
| Customers in Germany | 2.0 times France and Spain |
| Women | 1.5 times men |

These are associations in the data, not proven causes. See `docs/churn_drivers_and_recommendations.md` for the explanation and five retention recommendations.

## Dashboard

- **Risk Calculator:** enter a customer's details to get a churn probability, a Low/Medium/High label and a follow-up flag.
- **Distribution:** how predicted risk is spread across customers, with the threshold marked.
- **Feature Importance:** what drives the model's predictions (importance and SHAP).
- **What-If Simulator:** change activity, products, balance or tenure and see the risk before and after.

## Project structure

```
data/        raw data (European_Bank.csv), clean data, train/test sets
notebooks/   01 data audit, 02 EDA, 04 models, 05 final model, 06 explainability
src/         preprocess.py (pipeline), train_final.py, and check scripts
models/      final_model.joblib (pipeline + threshold)
app/         app.py (Streamlit dashboard)
reports/     result tables and figures/
docs/        data audit, EDA findings, model justification, drivers and recommendations
```

## Run it locally (Windows PowerShell)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/preprocess.py        # builds train/test sets
python src/train_final.py       # rebuilds the final model
streamlit run app/app.py
```

## Method notes

- One scikit-learn pipeline (feature engineering, encoding, optional scaling) is used in training and in the app, so predictions match.
- Encoders and scalers are fitted on training data only to prevent data leakage; the split is stratified 80/20 with a fixed random state.
- Engineered features: balance-to-salary ratio, product density, engagement x products, age x tenure, age / tenure.

## Limitations

Single dataset, no time dimension, estimated salary may be synthetic, and results may not generalise to other banks. The dashboard is a demonstration and should not be used for real customer decisions.

## Data source

European_Bank.csv (10,000 retail bank customer records) was downloaded from the project portal of the author's company in October 2026. It is a practice dataset.
