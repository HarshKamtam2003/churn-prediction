r"""Print model probabilities for a few test customers, to compare with the app.
Run from the project folder:   python src/check_predictions.py
"""
import joblib
import pandas as pd

from preprocess import ROOT

FEATURES = ["CreditScore", "Geography", "Gender", "Age", "Tenure", "Balance",
            "NumOfProducts", "HasCrCard", "IsActiveMember", "EstimatedSalary"]

art = joblib.load(ROOT / "models" / "final_model.joblib")
test = pd.read_csv(ROOT / "data" / "test.csv")
test["prob"] = art["pipeline"].predict_proba(test[FEATURES])[:, 1]

print("First 5 test customers (row number, probability):")
for i in range(5):
    print(f"  row {i}: {test.prob.iloc[i]:.4f}")
top = int(test.prob.idxmax())
print(f"\nHighest-risk test customer: row {top}, probability {test.prob.iloc[top]:.4f}")
print(test.loc[top, FEATURES].to_dict())
print(f"\nThreshold: {art['threshold']:.2f}")
