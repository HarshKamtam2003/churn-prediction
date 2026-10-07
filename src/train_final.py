r"""Rebuild the locked final model inside the project environment.

Same settings as Day 5 (tuned XGBoost, threshold from cross-validated predictions).
Run from the project folder:   python src/train_final.py
It saves models/final_model.joblib, which the Streamlit app loads.
"""
import joblib
import numpy as np
from sklearn.metrics import f1_score, precision_recall_curve, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from preprocess import ROOT, build_preprocessor, load_data, split_data

# Best settings found by the Day 5 search
PARAMS = dict(
    n_estimators=300, max_depth=3, learning_rate=0.03,
    subsample=0.8, colsample_bytree=0.85,
    random_state=42, eval_metric="logloss", n_jobs=1,
)

if __name__ == "__main__":
    X_train, X_test, y_train, y_test = split_data(load_data())
    pipe = Pipeline([("prep", build_preprocessor(scale=False)), ("model", XGBClassifier(**PARAMS))])

    # Threshold from cross-validated predictions on the training data only (as in Day 5)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof = cross_val_predict(pipe, X_train, y_train, cv=cv, method="predict_proba")[:, 1]
    prec, rec, thr = precision_recall_curve(y_train, oof)
    f1s = 2 * prec * rec / (prec + rec + 1e-9)
    threshold = float(thr[int(np.argmax(f1s[:-1]))])

    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= threshold).astype(int)
    print(f"Test ROC-AUC: {roc_auc_score(y_test, proba):.3f}  (Day 5: 0.871)")
    print(f"Threshold:    {threshold:.2f}  (Day 5: 0.29)")
    print(f"Precision {precision_score(y_test, pred):.3f} | Recall {recall_score(y_test, pred):.3f} | F1 {f1_score(y_test, pred):.3f}")

    joblib.dump({"pipeline": pipe, "threshold": threshold, "model_name": "XGBoost"},
                ROOT / "models" / "final_model.joblib")
    print("Saved models/final_model.joblib")
