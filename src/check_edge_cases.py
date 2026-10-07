r"""Run unusual customers through the final model and check the results are sensible.
Run from the project folder:   python src/check_edge_cases.py
"""
import joblib
import numpy as np
import pandas as pd

from preprocess import ROOT

art = joblib.load(ROOT / "models" / "final_model.joblib")
pipe, threshold = art["pipeline"], art["threshold"]

base = dict(CreditScore=650, Geography="France", Gender="Female", Age=40, Tenure=5, Balance=80000.0,
            NumOfProducts=2, HasCrCard=1, IsActiveMember=1, EstimatedSalary=100000.0)
cases = {
    "Typical customer": {},
    "Tenure = 0": dict(Tenure=0),
    "Balance = 0": dict(Balance=0.0),
    "4 products": dict(NumOfProducts=4),
    "Very young (18)": dict(Age=18),
    "Very old (92)": dict(Age=92),
    "Salary = 0": dict(EstimatedSalary=0.0),
    "Tenure 0 + Balance 0 + 4 products": dict(Tenure=0, Balance=0.0, NumOfProducts=4),
    "Lowest credit score (350)": dict(CreditScore=350),
}
ok = True
print(f"{'Case':36s} {'Probability':>11s}  Flag")
for name, change in cases.items():
    p = float(pipe.predict_proba(pd.DataFrame([{**base, **change}]))[:, 1][0])
    good = np.isfinite(p) and 0 <= p <= 1
    ok &= good
    print(f"{name:36s} {p:11.4f}  {'Yes' if p >= threshold else 'No'}{'' if good else '  <-- PROBLEM'}")
print("\nAll cases produced valid probabilities." if ok else "\nSome cases failed, see above.")
