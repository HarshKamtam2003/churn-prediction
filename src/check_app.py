r"""Automatic check that the app shows the same predictions as the model.
Run from the project folder:   python src/check_app.py
"""
import joblib
import pandas as pd
from streamlit.testing.v1 import AppTest

from preprocess import ROOT

FEATURES = ["CreditScore", "Geography", "Gender", "Age", "Tenure", "Balance",
            "NumOfProducts", "HasCrCard", "IsActiveMember", "EstimatedSalary"]
pipe = joblib.load(ROOT / "models" / "final_model.joblib")["pipeline"]
test = pd.read_csv(ROOT / "data" / "test.csv")

at = AppTest.from_file(str(ROOT / "app" / "app.py"), default_timeout=180).run()
all_ok = not at.exception
print("App starts without errors:", "PASS" if all_ok else "FAIL")

print("\n1. App probability vs model probability")
for i in [0, 1, 2, 3, 4, 501]:
    at.number_input(key="row_idx").set_value(i).run()
    at.button[0].click().run()
    shown = [c.value for c in at.caption if c.value.startswith("Exact probability")]
    expected = float(pipe.predict_proba(test[FEATURES].iloc[[i]])[:, 1][0])
    ok = bool(shown) and shown[0] == f"Exact probability: {expected:.4f}"
    all_ok &= ok
    print(f"   row {i:>3}: app {shown[0].split(': ')[1] if shown else 'n/a'} | model {expected:.4f} | {'PASS' if ok else 'FAIL'}")

print("\n2. 'Loaded test customer' note disappears after editing an input")
at.number_input(key="row_idx").set_value(5).run()
at.button[0].click().run()
shown_before = any("Loaded test customer" in c.value for c in at.caption)
at.slider(key="in_Age").set_value(at.slider(key="in_Age").value + 1).run()
shown_after = any("Loaded test customer" in c.value for c in at.caption)
ok = shown_before and not shown_after
all_ok &= ok
print(f"   note shown after loading: {shown_before} | after editing: {shown_after} | {'PASS' if ok else 'FAIL (download the latest app.py again)'}")

print("\n3. Every page opens without errors")
for page in ["Risk Calculator", "Distribution", "Feature Importance", "What-If Simulator"]:
    at.sidebar.radio[0].set_value(page).run()
    ok = not at.exception
    all_ok &= ok
    print(f"   {page:20s} {'PASS' if ok else 'FAIL'}")

print("\nALL CHECKS PASSED" if all_ok else "\nSOME CHECKS FAILED, see above")
