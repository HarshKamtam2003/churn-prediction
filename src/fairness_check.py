r"""Check how the final model treats groups, on the test set (for the paper's responsible-use section).
Run from the project folder:   python src/fairness_check.py
Saves reports/day9_fairness.csv
"""
import joblib
import pandas as pd

from preprocess import ROOT

FEATURES = ["CreditScore", "Geography", "Gender", "Age", "Tenure", "Balance",
            "NumOfProducts", "HasCrCard", "IsActiveMember", "EstimatedSalary"]
art = joblib.load(ROOT / "models" / "final_model.joblib")
test = pd.read_csv(ROOT / "data" / "test.csv")
test["prob"] = art["pipeline"].predict_proba(test[FEATURES])[:, 1]
test["flag"] = (test["prob"] >= art["threshold"]).astype(int)
y, f = test["Exited"], test["flag"]

tp, fp = int(((f == 1) & (y == 1)).sum()), int(((f == 1) & (y == 0)).sum())
fn, tn = int(((f == 0) & (y == 1)).sum()), int(((f == 0) & (y == 0)).sum())
print(f"Threshold {art['threshold']:.2f} | test customers {len(test)} | actual churners {int(y.sum())}")
print(f"Confusion matrix: caught {tp}, false alarms {fp}, missed {fn}, correctly left alone {tn}\n")

rows = []
for col in ["Gender", "Geography"]:
    for g, d in test.groupby(col):
        t, fl = d["Exited"], d["flag"]
        caught = int(((fl == 1) & (t == 1)).sum())
        flagged = int(fl.sum())
        rows.append({"Group": f"{col}: {g}", "Customers": len(d),
                     "Actual churn %": round(100 * t.mean(), 1),
                     "Flagged %": round(100 * fl.mean(), 1),
                     "Recall %": round(100 * caught / max(int(t.sum()), 1), 1),
                     "Precision %": round(100 * caught / max(flagged, 1), 1)})
out = pd.DataFrame(rows).set_index("Group")
print(out.to_string())
out.to_csv(ROOT / "reports" / "day9_fairness.csv")
print("\nSaved reports/day9_fairness.csv")
