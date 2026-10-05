r"""Reusable, leak-free preprocessing for the churn project.

Usage in a notebook:
    import sys; sys.path.append(r"<project folder>\src")
    from preprocess import prepare_data
    X_train, X_test, y_train, y_test, pipe = prepare_data(scale=False)

Run as a script to save the train/test sets and the fitted pipeline:
    python src/preprocess.py
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "churn_clean.csv"
TARGET = "Exited"
DROP_COLS = ["RowNumber", "CustomerId", "Surname", "Year"]
CATEGORICAL = ["Geography", "Gender"]
NUMERIC = [
    "CreditScore", "Age", "Tenure", "Balance", "NumOfProducts", "EstimatedSalary",
    "BalanceSalaryRatio", "ProductDensity", "EngagementProduct", "AgeTenure", "AgeByTenure",
]
BINARY = ["HasCrCard", "IsActiveMember"]
RANDOM_STATE = 42


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create engineered features. Uses no statistics from the data, so it cannot leak."""
    df = df.copy()
    salary = df["EstimatedSalary"].replace(0, np.nan)
    df["BalanceSalaryRatio"] = (df["Balance"] / salary).fillna(0)
    # Tenure + 1 avoids division by zero when Tenure = 0
    df["ProductDensity"] = df["NumOfProducts"] / (df["Tenure"] + 1)
    df["EngagementProduct"] = df["IsActiveMember"] * df["NumOfProducts"]
    df["AgeTenure"] = df["Age"] * df["Tenure"]
    df["AgeByTenure"] = df["Age"] / (df["Tenure"] + 1)
    return df


def build_preprocessor(scale: bool = False) -> Pipeline:
    """Feature engineering + one-hot encoding (+ optional scaling).

    scale=True for Logistic Regression; scale=False for tree models.
    Fitting happens on training data only (call .fit on X_train).
    """
    numeric_step = StandardScaler() if scale else "passthrough"
    columns = ColumnTransformer(
        [
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False), CATEGORICAL),
            ("num", numeric_step, NUMERIC),
            ("bin", "passthrough", BINARY),
        ],
        verbose_feature_names_out=False,
    )
    pipe = Pipeline([("features", FunctionTransformer(add_features)), ("columns", columns)])
    pipe.set_output(transform="pandas")
    return pipe


def load_data(path=DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    if df.isnull().sum().sum() > 0:
        raise ValueError("Dataset contains missing values; handle them before modelling.")
    return df


def split_data(df: pd.DataFrame, test_size: float = 0.2):
    """Stratified 80/20 split with a fixed random_state."""
    X, y = df.drop(columns=[TARGET]), df[TARGET]
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE)


def prepare_data(path=DATA_PATH, scale: bool = False):
    """Raw CSV -> model-ready train/test features. Returns X_train, X_test, y_train, y_test, fitted pipeline."""
    df = load_data(path)
    X_train, X_test, y_train, y_test = split_data(df)
    pipe = build_preprocessor(scale=scale)
    X_train_t = pipe.fit_transform(X_train)  # fit on train only
    X_test_t = pipe.transform(X_test)        # test is only transformed
    return X_train_t, X_test_t, y_train, y_test, pipe


if __name__ == "__main__":
    # Import under the module name so saved pipelines can be loaded later (e.g. in Streamlit)
    import preprocess as pp

    build_preprocessor = pp.build_preprocessor
    df = load_data()
    X_train, X_test, y_train, y_test = split_data(df)
    pd.concat([X_train, y_train], axis=1).to_csv(ROOT / "data" / "train.csv", index=False)
    pd.concat([X_test, y_test], axis=1).to_csv(ROOT / "data" / "test.csv", index=False)
    (ROOT / "models").mkdir(exist_ok=True)
    for name, scale in [("preprocessor_trees.joblib", False), ("preprocessor_scaled.joblib", True)]:
        joblib.dump(build_preprocessor(scale).fit(X_train), ROOT / "models" / name)
    print(f"Train: {X_train.shape}, churn {y_train.mean():.3%}")
    print(f"Test:  {X_test.shape}, churn {y_test.mean():.3%}")
